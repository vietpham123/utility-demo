using Npgsql;
using Confluent.Kafka;
using StackExchange.Redis;
using System.Text.Json;

public class ScadaSimulatorService : BackgroundService
{
    private readonly ILogger<ScadaSimulatorService> _logger;
    private readonly ScadaDataStore _store;
    private readonly string _dbConn;
    private readonly string _kafkaBroker;
    private readonly string _redisConn;
    private IProducer<string, string>? _producer;
    private IConnectionMultiplexer? _redis;
    private readonly Random _rng = new();
    public bool IsReady { get; private set; }
    private int _batchCount = 0;
    private int _errorCount = 0;

    public ScadaSimulatorService(ILogger<ScadaSimulatorService> logger, ScadaDataStore store)
    {
        _logger = logger;
        _store = store;
        var dbHost = Environment.GetEnvironmentVariable("DB_HOST") ?? "timescaledb";
        var dbPort = Environment.GetEnvironmentVariable("DB_PORT") ?? "5432";
        var dbName = Environment.GetEnvironmentVariable("DB_NAME") ?? "utilitydb";
        var dbUser = Environment.GetEnvironmentVariable("DB_USER") ?? "utilityuser";
        var dbPass = Environment.GetEnvironmentVariable("DB_PASSWORD") ?? "<DB_PASSWORD>";
        _dbConn = $"Host={dbHost};Port={dbPort};Database={dbName};Username={dbUser};Password={dbPass}";
        _kafkaBroker = Environment.GetEnvironmentVariable("KAFKA_BROKER") ?? "kafka:9092";
        _redisConn = Environment.GetEnvironmentVariable("REDIS_HOST") ?? "redis";
    }

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        _logger.LogInformation("SCADA Simulator starting...");
        await Task.Delay(15000, ct); // Wait for infrastructure

        // Initialize sensors for all substations, feeders, transformers
        InitializeSensors();

        // Connect to Kafka
        try
        {
            var config = new ProducerConfig { BootstrapServers = _kafkaBroker, Acks = Acks.Leader };
            _producer = new ProducerBuilder<string, string>(config).Build();
            _logger.LogInformation("Kafka producer connected");
        }
        catch (Exception ex)
        {
            _logger.LogWarning("Kafka not available, continuing without streaming: {Error}", ex.Message);
        }

        // Connect to Redis
        try
        {
            _redis = await ConnectionMultiplexer.ConnectAsync($"{_redisConn},abortConnect=false,connectTimeout=5000");
            _logger.LogInformation("Redis connected");
        }
        catch (Exception ex)
        {
            _logger.LogWarning("Redis not available, continuing without cache: {Error}", ex.Message);
        }

        IsReady = true;
        _logger.LogInformation("SCADA Simulator ready with {Count} sensors", _store.Sensors.Count);

        // Main simulation loop: generate readings every 10-20 seconds
        while (!ct.IsCancellationRequested)
        {
            try
            {
                await GenerateReadingsBatch(ct);
            }
            catch (Exception ex)
            {
                _logger.LogError("SCADA simulation error: {Error}", ex.Message);
            }
            await Task.Delay(10000 + _rng.Next(10000), ct);
        }
    }

    private void InitializeSensors()
    {
        // Substation sensors
        var substations = new[] {
            (1, "Lakeside Substation", 138.0, 2000.0, "Chicago, IL"),
            (2, "Harbor Point Substation", 138.0, 1800.0, "Baltimore, MD"),
            (3, "Liberty Grid Substation", 230.0, 2500.0, "Philadelphia, PA"),
            (4, "Gateway Arch Substation", 138.0, 1600.0, "St. Louis, MO"),
            (5, "North Star Substation", 230.0, 2200.0, "Minneapolis, MN"),
            (6, "Motor City Substation", 138.0, 1900.0, "Detroit, MI"),
            (7, "Empire State Substation", 230.0, 3000.0, "New York, NY"),
            (8, "Peachtree Substation", 138.0, 1700.0, "Atlanta, GA"),
            (9, "Sunshine Substation", 138.0, 2100.0, "Miami, FL"),
            (10, "Lone Star Substation", 230.0, 2400.0, "Dallas, TX")
        };
        foreach (var (id, name, voltage, current, loc) in substations)
        {
            _store.Sensors[$"SCADA-SUB-{id:D3}"] = new SensorConfig
            {
                SensorId = $"SCADA-SUB-{id:D3}", EquipmentType = "Substation", EquipmentId = id,
                EquipmentName = name, NominalVoltageKv = voltage, MaxCurrentA = current, Location = loc
            };
        }

        // Feeder sensors (12 feeders)
        var feederVoltages = new[] { 13.2, 13.2, 13.2, 4.16, 13.2, 13.2, 4.16, 13.2, 34.5, 13.2, 13.2, 4.16 };
        var feederCurrents = new[] { 600.0, 600.0, 800.0, 400.0, 600.0, 800.0, 400.0, 600.0, 1000.0, 800.0, 600.0, 400.0 };
        for (int i = 1; i <= 12; i++)
        {
            _store.Sensors[$"SCADA-FDR-{i:D3}"] = new SensorConfig
            {
                SensorId = $"SCADA-FDR-{i:D3}", EquipmentType = "Feeder", EquipmentId = i,
                EquipmentName = $"Feeder {i}", NominalVoltageKv = feederVoltages[i - 1],
                MaxCurrentA = feederCurrents[i - 1]
            };
        }

        // Key transformer sensors (12 of the 36, the larger ones)
        var keyTransformers = new[] { 3, 7, 8, 13, 16, 22, 23, 25, 26, 27, 28, 31 };
        foreach (var tid in keyTransformers)
        {
            _store.Sensors[$"SCADA-TRX-{tid:D3}"] = new SensorConfig
            {
                SensorId = $"SCADA-TRX-{tid:D3}", EquipmentType = "Transformer", EquipmentId = tid,
                EquipmentName = $"Transformer {tid}", NominalVoltageKv = 13.2, MaxCurrentA = 300.0
            };
        }

        _logger.LogInformation("Initialized {Count} SCADA sensors", _store.Sensors.Count);
    }

    public async Task GenerateReadingsBatch(CancellationToken ct)
    {
        _batchCount++;
        _logger.LogDebug("Starting SCADA batch #{Batch}, sensors={Count}", _batchCount, _store.Sensors.Count);

        // ~6% chance: simulate sensor communication timeout
        if (_rng.NextDouble() < 0.06)
        {
            _errorCount++;
            var faultySensor = _store.Sensors.Values.ElementAt(_rng.Next(_store.Sensors.Count));
            _logger.LogError("Sensor communication timeout: {SensorId} on {Equipment} - no response within 5000ms. " +
                "Total errors: {ErrorCount}, Batch: {Batch}",
                faultySensor.SensorId, faultySensor.EquipmentName, _errorCount, _batchCount);
            throw new TimeoutException($"SCADA sensor {faultySensor.SensorId} communication timeout after 5000ms");
        }

        // ~4% chance: simulate data acquisition unit (DAU) failure
        if (_rng.NextDouble() < 0.04)
        {
            _errorCount++;
            _logger.LogError("Data Acquisition Unit failure detected - partial batch will be generated. " +
                "Affected substation: SUB-{SubId}, ErrorCount: {ErrorCount}",
                _rng.Next(1, 4), _errorCount);
        }

        var now = DateTime.UtcNow;
        var hour = now.Hour;
        var loadFactor = (hour >= 8 && hour <= 20) ? 0.7 + _rng.NextDouble() * 0.25 : 0.3 + _rng.NextDouble() * 0.3;
        var readings = new List<ScadaReading>();
        var alerts = new List<ScadaAlert>();

        foreach (var sensor in _store.Sensors.Values)
        {
            var reading = new ScadaReading
            {
                Time = now,
                SensorId = sensor.SensorId,
                EquipmentType = sensor.EquipmentType,
                EquipmentId = sensor.EquipmentId,
                FrequencyHz = Math.Round(59.95 + _rng.NextDouble() * 0.1, 4),
                PowerFactor = Math.Round(0.85 + _rng.NextDouble() * 0.14, 4),
                TemperatureC = Math.Round(25 + _rng.NextDouble() * 40 + loadFactor * 15, 2)
            };

            // Voltage: fluctuate around nominal ±5%
            var voltageNoise = 1.0 + (_rng.NextDouble() - 0.5) * 0.10;
            reading.VoltageKv = Math.Round(sensor.NominalVoltageKv * voltageNoise, 4);

            // Current: based on load factor
            reading.CurrentA = Math.Round(sensor.MaxCurrentA * loadFactor * (0.5 + _rng.NextDouble() * 0.5), 4);

            // Power calculations
            reading.ActivePowerKw = Math.Round(reading.VoltageKv * reading.CurrentA * reading.PowerFactor * 1.732, 4);
            reading.ReactivePowerKvar = Math.Round(reading.ActivePowerKw * Math.Tan(Math.Acos(reading.PowerFactor)), 4);

            // Check for alert conditions (~3% chance of anomaly per sensor per cycle)
            if (_rng.NextDouble() < 0.03)
            {
                var anomalyType = _rng.Next(4);
                switch (anomalyType)
                {
                    case 0: // Voltage sag
                        reading.VoltageKv = Math.Round(sensor.NominalVoltageKv * (0.85 + _rng.NextDouble() * 0.05), 4);
                        reading.Status = "Warning";
                        alerts.Add(CreateAlert(sensor, "Voltage Sag", "Warning", reading.VoltageKv, sensor.NominalVoltageKv * 0.9,
                            $"Voltage drop detected: {reading.VoltageKv}kV (nominal: {sensor.NominalVoltageKv}kV)"));
                        break;
                    case 1: // Overcurrent
                        reading.CurrentA = Math.Round(sensor.MaxCurrentA * (0.9 + _rng.NextDouble() * 0.2), 4);
                        reading.Status = "Warning";
                        alerts.Add(CreateAlert(sensor, "Overcurrent", "High", reading.CurrentA, sensor.MaxCurrentA * 0.85,
                            $"Current approaching limit: {reading.CurrentA}A (max: {sensor.MaxCurrentA}A)"));
                        break;
                    case 2: // Temperature high
                        reading.TemperatureC = Math.Round(75 + _rng.NextDouble() * 20, 2);
                        reading.Status = "Warning";
                        alerts.Add(CreateAlert(sensor, "High Temperature", "Medium", reading.TemperatureC, 70.0,
                            $"Equipment temperature elevated: {reading.TemperatureC}°C"));
                        break;
                    case 3: // Frequency deviation
                        reading.FrequencyHz = Math.Round(59.85 + _rng.NextDouble() * 0.05, 4);
                        reading.Status = "Warning";
                        alerts.Add(CreateAlert(sensor, "Frequency Deviation", "High", reading.FrequencyHz, 59.95,
                            $"Frequency below normal: {reading.FrequencyHz}Hz"));
                        break;
                }
            }

            readings.Add(reading);
            _store.AddReading(reading);
        }

        foreach (var alert in alerts) _store.AddAlert(alert);

        _logger.LogDebug("Generated {ReadingCount} readings with {AlertCount} alerts, loadFactor={LoadFactor:F2}",
            readings.Count, alerts.Count, loadFactor);

        // Persist to TimescaleDB
        await PersistReadings(readings, ct);
        _logger.LogDebug("Persisted {Count} readings to TimescaleDB", readings.Count);

        if (alerts.Count > 0)
        {
            await PersistAlerts(alerts, ct);
            _logger.LogDebug("Persisted {Count} alerts to TimescaleDB", alerts.Count);
        }

        // Publish to Kafka
        await PublishToKafka(readings, alerts, ct);
        _logger.LogDebug("Published readings and alerts to Kafka topics");

        // Update Redis cache
        await UpdateRedisCache(readings, ct);
        _logger.LogDebug("Updated Redis cache with {Count} sensor readings", readings.Count);

        _logger.LogInformation("SCADA batch: {Readings} readings, {Alerts} alerts",
            readings.Count, alerts.Count);
    }

    private ScadaAlert CreateAlert(SensorConfig sensor, string type, string severity, double value, double threshold, string msg)
    {
        return new ScadaAlert
        {
            Time = DateTime.UtcNow, SensorId = sensor.SensorId, EquipmentType = sensor.EquipmentType,
            EquipmentId = sensor.EquipmentId, AlertType = type, Severity = severity,
            Value = value, Threshold = threshold, Message = msg
        };
    }

    private async Task PersistReadings(List<ScadaReading> readings, CancellationToken ct)
    {
        try
        {
            await using var conn = new NpgsqlConnection(_dbConn);
            await conn.OpenAsync(ct);
            await using var writer = await conn.BeginBinaryImportAsync(
                "COPY timeseries.scada_readings (time, sensor_id, equipment_type, equipment_id, voltage_kv, current_a, frequency_hz, power_factor, temperature_c, active_power_kw, reactive_power_kvar, status) FROM STDIN (FORMAT BINARY)", ct);
            foreach (var r in readings)
            {
                await writer.StartRowAsync(ct);
                await writer.WriteAsync(r.Time, NpgsqlTypes.NpgsqlDbType.TimestampTz, ct);
                await writer.WriteAsync(r.SensorId, NpgsqlTypes.NpgsqlDbType.Varchar, ct);
                await writer.WriteAsync(r.EquipmentType, NpgsqlTypes.NpgsqlDbType.Varchar, ct);
                await writer.WriteAsync(r.EquipmentId, NpgsqlTypes.NpgsqlDbType.Integer, ct);
                await writer.WriteAsync((decimal)r.VoltageKv, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.CurrentA, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.FrequencyHz, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.PowerFactor, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.TemperatureC, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.ActivePowerKw, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync((decimal)r.ReactivePowerKvar, NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync(r.Status, NpgsqlTypes.NpgsqlDbType.Varchar, ct);
            }
            await writer.CompleteAsync(ct);
        }
        catch (Exception ex)
        {
            _logger.LogWarning("DB persist error (readings): {Error}", ex.Message);
        }
    }

    private async Task PersistAlerts(List<ScadaAlert> alerts, CancellationToken ct)
    {
        try
        {
            await using var conn = new NpgsqlConnection(_dbConn);
            await conn.OpenAsync(ct);
            foreach (var a in alerts)
            {
                await using var cmd = new NpgsqlCommand(
                    "INSERT INTO timeseries.scada_alerts (time, sensor_id, equipment_type, equipment_id, alert_type, severity, value, threshold, message) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)", conn);
                cmd.Parameters.AddWithValue(a.Time);
                cmd.Parameters.AddWithValue(a.SensorId);
                cmd.Parameters.AddWithValue(a.EquipmentType);
                cmd.Parameters.AddWithValue(a.EquipmentId);
                cmd.Parameters.AddWithValue(a.AlertType);
                cmd.Parameters.AddWithValue(a.Severity);
                cmd.Parameters.AddWithValue((decimal)a.Value);
                cmd.Parameters.AddWithValue((decimal)a.Threshold);
                cmd.Parameters.AddWithValue(a.Message);
                await cmd.ExecuteNonQueryAsync(ct);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning("DB persist error (alerts): {Error}", ex.Message);
        }
    }

    private async Task PublishToKafka(List<ScadaReading> readings, List<ScadaAlert> alerts, CancellationToken ct)
    {
        if (_producer == null) return;
        try
        {
            foreach (var r in readings)
            {
                var json = JsonSerializer.Serialize(r);
                await _producer.ProduceAsync("scada.telemetry", new Message<string, string> { Key = r.SensorId, Value = json }, ct);
            }
            foreach (var a in alerts)
            {
                var json = JsonSerializer.Serialize(a);
                await _producer.ProduceAsync("scada.alerts", new Message<string, string> { Key = a.SensorId, Value = json }, ct);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning("Kafka publish error: {Error}", ex.Message);
        }
    }

    private async Task UpdateRedisCache(List<ScadaReading> readings, CancellationToken ct)
    {
        if (_redis == null || !_redis.IsConnected) return;
        try
        {
            var db = _redis.GetDatabase();
            foreach (var r in readings)
            {
                var json = JsonSerializer.Serialize(r);
                await db.StringSetAsync($"scada:latest:{r.SensorId}", json, TimeSpan.FromMinutes(2));
            }
            await db.StringSetAsync("scada:last_update", DateTime.UtcNow.ToString("o"), TimeSpan.FromMinutes(5));
        }
        catch { }
    }
}
