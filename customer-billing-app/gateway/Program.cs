using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using BillingGateway.Controllers;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddHttpClient();
builder.Services.AddHostedService<DataSimulatorService>();
var app = builder.Build();
app.MapControllers();
app.Run();
