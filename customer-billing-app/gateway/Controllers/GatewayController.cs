using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;

namespace BillingGateway.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class GatewayController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ILogger<GatewayController> _logger;

        public GatewayController(IHttpClientFactory httpClientFactory, ILogger<GatewayController> logger)
        {
            _httpClientFactory = httpClientFactory;
            _logger = logger;
        }

        [HttpGet("customers")]
        public async Task<IActionResult> GetCustomers()
        {
            _logger.LogInformation("Gateway: proxying GET /api/gateway/customers");
            var client = _httpClientFactory.CreateClient();
            var response = await client.GetStringAsync("http://customer-service/api/customers");
            return Content(response, "application/json");
        }

        [HttpGet("customers/{id}")]
        public async Task<IActionResult> GetCustomerById(int id)
        {
            _logger.LogInformation("Gateway: proxying GET /api/gateway/customers/{Id}", id);
            var client = _httpClientFactory.CreateClient();
            var response = await client.GetStringAsync($"http://customer-service/api/customers/{id}");
            return Content(response, "application/json");
        }

        [HttpGet("invoices")]
        public async Task<IActionResult> GetInvoices([FromQuery] int? customerId)
        {
            var url = customerId.HasValue
                ? $"http://invoice-service/api/invoices?customerId={customerId}"
                : "http://invoice-service/api/invoices";
            _logger.LogInformation("Gateway: proxying GET invoices, url={Url}", url);
            var client = _httpClientFactory.CreateClient();
            var response = await client.GetStringAsync(url);
            return Content(response, "application/json");
        }

        [HttpGet("payments")]
        public async Task<IActionResult> GetPayments([FromQuery] int? customerId)
        {
            var url = customerId.HasValue
                ? $"http://payment-service/api/payments?customerId={customerId}"
                : "http://payment-service/api/payments";
            _logger.LogInformation("Gateway: proxying GET payments, url={Url}", url);
            var client = _httpClientFactory.CreateClient();
            var response = await client.GetStringAsync(url);
            return Content(response, "application/json");
        }

        [HttpPost("payments")]
        public async Task<IActionResult> CreatePayment()
        {
            _logger.LogInformation("Gateway: proxying POST /api/gateway/payments");
            var client = _httpClientFactory.CreateClient();
            using var reader = new System.IO.StreamReader(Request.Body);
            var body = await reader.ReadToEndAsync();
            var content = new StringContent(body, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("http://payment-service/api/payments", content);
            var result = await response.Content.ReadAsStringAsync();
            return Content(result, "application/json");
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { Status = "Healthy", Service = "BillingGateway" });
        }
    }

    public class DataSimulatorService : BackgroundService
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ILogger<DataSimulatorService> _logger;
        private readonly Random _rng = new();
        private static readonly string[] _methods = { "Credit Card", "Bank Transfer", "Auto Pay", "ACH Direct" };
        private static readonly string[] _prefixes = { "PAY-CC", "PAY-BT", "PAY-AP", "PAY-ACH" };

        public DataSimulatorService(IHttpClientFactory httpClientFactory, ILogger<DataSimulatorService> logger)
        {
            _httpClientFactory = httpClientFactory;
            _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
            _logger.LogInformation("DataSimulator: Starting payment simulation loop");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    int custId = _rng.Next(1, 31);
                    int methodIdx = _rng.Next(_methods.Length);
                    var payment = new
                    {
                        invoiceId = 1001 + _rng.Next(0, 180),
                        customerId = custId,
                        accountNumber = $"ACCT-{10000 + custId}",
                        amount = Math.Round(50 + _rng.NextDouble() * 500, 2),
                        paymentDate = DateTime.UtcNow.ToString("yyyy-MM-dd"),
                        method = _methods[methodIdx],
                        confirmationNumber = $"{_prefixes[methodIdx]}-{_rng.Next(10000, 99999)}",
                        status = _rng.NextDouble() > 0.1 ? "Completed" : "Failed"
                    };

                    var client = _httpClientFactory.CreateClient();
                    var json = JsonSerializer.Serialize(payment);
                    var content = new StringContent(json, Encoding.UTF8, "application/json");
                    await client.PostAsync("http://payment-service/api/payments", content);

                    _logger.LogInformation("DataSimulator: Generated payment for customer {CustId}, amount=${Amount}", custId, payment.amount);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning("DataSimulator: Error generating payment - {Error}", ex.Message);
                }

                int delaySeconds = 45 + _rng.Next(90);
                await Task.Delay(TimeSpan.FromSeconds(delaySeconds), stoppingToken);
            }
        }
    }
}
