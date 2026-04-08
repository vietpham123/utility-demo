using Microsoft.AspNetCore.Mvc;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Gateway.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class GatewayController : ControllerBase
    {
        private static readonly ILogger _logger = LoggerFactory.CreateLogger<GatewayController>();
        private readonly HttpClient _httpClient;
        public GatewayController(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        [HttpGet("customers")]
        public async Task<IActionResult> GetCustomers()
        {
            _logger.LogInformation("Gateway: GET /api/gateway/customers called");
            var response = await _httpClient.GetStringAsync("http://localhost:5001/api/customers");
            return Content(response, "application/json");
        }
        [HttpGet("invoices")]
        public async Task<IActionResult> GetInvoices()
        {
            _logger.LogInformation("Gateway: GET /api/gateway/invoices called");
            var response = await _httpClient.GetStringAsync("http://localhost:5002/api/invoices");
            return Content(response, "application/json");
        }
        [HttpGet("payments")]
        public async Task<IActionResult> GetPayments()
        {
            _logger.LogInformation("Gateway: GET /api/gateway/payments called");
            var response = await _httpClient.GetStringAsync("http://localhost:5003/api/payments");
            return Content(response, "application/json");
        }
    }
}
