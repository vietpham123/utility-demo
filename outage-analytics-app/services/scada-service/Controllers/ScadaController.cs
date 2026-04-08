using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/scada")]
public class ScadaController : ControllerBase
{
    private readonly ScadaDataStore _store;
    private readonly ScadaSimulatorService _simulator;
    private readonly ILogger<ScadaController> _logger;

    public ScadaController(ScadaDataStore store, ScadaSimulatorService simulator, ILogger<ScadaController> logger)
    {
        _store = store;
        _simulator = simulator;
        _logger = logger;
    }

    [HttpGet("sensors")]
    public IActionResult GetSensors()
    {
        _logger.LogInformation("GET /api/scada/sensors");
        return Ok(_store.Sensors.Values.ToList());
    }

    [HttpGet("readings/latest")]
    public IActionResult GetLatestReadings()
    {
        // ~3% chance: simulate LINQ query timeout on large dataset
        if (new Random().NextDouble() < 0.03)
        {
            _logger.LogError("LINQ aggregation timeout on RecentReadings - dataset size: {Count} readings",
                _store.RecentReadings.Count);
            return StatusCode(500, new { error = "Query timeout on readings aggregation" });
        }

        var latest = _store.RecentReadings
            .GroupBy(r => r.SensorId)
            .Select(g => g.Last())
            .OrderBy(r => r.SensorId)
            .ToList();
        _logger.LogInformation("GET /api/scada/readings/latest count={Count}", latest.Count);
        _logger.LogDebug("Latest readings breakdown: normal={Normal}, warning={Warning}",
            latest.Count(r => r.Status == "Normal"), latest.Count(r => r.Status == "Warning"));
        return Ok(latest);
    }

    [HttpGet("readings/history")]
    public IActionResult GetReadingHistory([FromQuery] string? sensorId, [FromQuery] int limit = 100)
    {
        var safeLimit = Math.Min(limit, 500);
        IEnumerable<ScadaReading> query = _store.RecentReadings;
        if (!string.IsNullOrEmpty(sensorId))
            query = query.Where(r => r.SensorId == sensorId);
        var result = query.Reverse().Take(safeLimit).ToList();
        _logger.LogInformation("GET /api/scada/readings/history sensorId={SensorId} count={Count}", sensorId, result.Count);
        return Ok(result);
    }

    [HttpGet("readings/equipment/{equipmentType}/{equipmentId}")]
    public IActionResult GetReadingsByEquipment(string equipmentType, int equipmentId, [FromQuery] int limit = 50)
    {
        var safeLimit = Math.Min(limit, 200);
        var result = _store.RecentReadings
            .Where(r => r.EquipmentType.Equals(equipmentType, StringComparison.OrdinalIgnoreCase) && r.EquipmentId == equipmentId)
            .Reverse().Take(safeLimit).ToList();
        return Ok(result);
    }

    [HttpGet("alerts")]
    public IActionResult GetAlerts([FromQuery] int limit = 50)
    {
        var safeLimit = Math.Min(limit, 200);
        var result = _store.RecentAlerts.Reverse().Take(safeLimit).ToList();
        _logger.LogInformation("GET /api/scada/alerts count={Count}", result.Count);
        return Ok(result);
    }

    [HttpGet("alerts/active")]
    public IActionResult GetActiveAlerts()
    {
        var result = _store.RecentAlerts.Where(a => !a.Acknowledged).Reverse().Take(50).ToList();
        return Ok(result);
    }

    [HttpGet("summary")]
    public IActionResult GetSummary()
    {
        var readings = _store.RecentReadings.ToList();
        var latest = readings.GroupBy(r => r.SensorId).Select(g => g.Last()).ToList();
        var avgVoltage = latest.Any() ? Math.Round(latest.Average(r => r.VoltageKv), 2) : 0;
        var avgFrequency = latest.Any() ? Math.Round(latest.Average(r => r.FrequencyHz), 4) : 0;
        var avgPowerFactor = latest.Any() ? Math.Round(latest.Average(r => r.PowerFactor), 4) : 0;
        var totalPowerMw = latest.Any() ? Math.Round(latest.Sum(r => r.ActivePowerKw) / 1000, 2) : 0;
        var warningCount = latest.Count(r => r.Status == "Warning");

        return Ok(new
        {
            sensorCount = _store.Sensors.Count,
            totalReadings = readings.Count,
            latestReadingsCount = latest.Count,
            averageVoltageKv = avgVoltage,
            averageFrequencyHz = avgFrequency,
            averagePowerFactor = avgPowerFactor,
            totalActivePowerMw = totalPowerMw,
            warningCount,
            alertCount = _store.RecentAlerts.Count,
            lastUpdate = latest.Any() ? latest.Max(r => r.Time).ToString("o") : null
        });
    }

    [HttpPost("simulate")]
    public async Task<IActionResult> Simulate()
    {
        if (!_simulator.IsReady)
        {
            _logger.LogWarning("POST /api/scada/simulate - simulator not ready, returning 503");
            return StatusCode(503, new { error = "SCADA simulator not yet initialized" });
        }

        _logger.LogInformation("POST /api/scada/simulate - triggering simulation cycle");

        try
        {
            await _simulator.GenerateReadingsBatch(HttpContext.RequestAborted);
        }
        catch (TimeoutException ex)
        {
            _logger.LogError(ex, "SCADA simulation failed with sensor timeout");
            return StatusCode(500, new { error = ex.Message, type = "SensorTimeout" });
        }

        var totalReadings = _store.RecentReadings.Count;
        var totalAlerts = _store.RecentAlerts.Count;
        _logger.LogDebug("Simulate response: sensors={Sensors}, readings={Readings}, alerts={Alerts}",
            _store.Sensors.Count, totalReadings, totalAlerts);

        return Ok(new
        {
            status = "Simulation cycle complete",
            sensorsProcessed = _store.Sensors.Count,
            totalReadings,
            alertCount = totalAlerts
        });
    }

    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new { status = "Healthy", service = "ScadaService", sensors = _store.Sensors.Count, readings = _store.RecentReadings.Count });
    }
}
