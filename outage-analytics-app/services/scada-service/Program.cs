var builder = WebApplication.CreateBuilder(args);
builder.Logging.SetMinimumLevel(LogLevel.Debug);
builder.Services.AddControllers();
builder.Services.AddSingleton<ScadaDataStore>();
builder.Services.AddSingleton<ScadaSimulatorService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<ScadaSimulatorService>());
var app = builder.Build();
app.MapControllers();
app.Run();
