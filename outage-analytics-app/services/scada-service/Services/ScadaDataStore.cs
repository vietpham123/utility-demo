using System.Collections.Concurrent;

public class ScadaDataStore
{
    public ConcurrentDictionary<string, SensorConfig> Sensors { get; } = new();
    public ConcurrentQueue<ScadaReading> RecentReadings { get; } = new();
    public ConcurrentQueue<ScadaAlert> RecentAlerts { get; } = new();
    private const int MaxReadings = 2000;
    private const int MaxAlerts = 500;

    public void AddReading(ScadaReading reading)
    {
        RecentReadings.Enqueue(reading);
        while (RecentReadings.Count > MaxReadings) RecentReadings.TryDequeue(out _);
    }

    public void AddAlert(ScadaAlert alert)
    {
        RecentAlerts.Enqueue(alert);
        while (RecentAlerts.Count > MaxAlerts) RecentAlerts.TryDequeue(out _);
    }
}

public class SensorConfig
{
    public string SensorId { get; set; } = "";
    public string EquipmentType { get; set; } = "";
    public int EquipmentId { get; set; }
    public string EquipmentName { get; set; } = "";
    public double NominalVoltageKv { get; set; }
    public double MaxCurrentA { get; set; }
    public string Location { get; set; } = "";
}

public class ScadaReading
{
    public DateTime Time { get; set; }
    public string SensorId { get; set; } = "";
    public string EquipmentType { get; set; } = "";
    public int EquipmentId { get; set; }
    public double VoltageKv { get; set; }
    public double CurrentA { get; set; }
    public double FrequencyHz { get; set; }
    public double PowerFactor { get; set; }
    public double TemperatureC { get; set; }
    public double ActivePowerKw { get; set; }
    public double ReactivePowerKvar { get; set; }
    public string Status { get; set; } = "Normal";
}

public class ScadaAlert
{
    public DateTime Time { get; set; }
    public string SensorId { get; set; } = "";
    public string EquipmentType { get; set; } = "";
    public int EquipmentId { get; set; }
    public string AlertType { get; set; } = "";
    public string Severity { get; set; } = "";
    public double Value { get; set; }
    public double Threshold { get; set; }
    public string Message { get; set; } = "";
    public bool Acknowledged { get; set; }
}
