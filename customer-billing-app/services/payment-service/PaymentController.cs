using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;

namespace PaymentService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PaymentsController : ControllerBase
    {
        private static readonly ILogger _logger = LoggerFactory.CreateLogger<PaymentsController>();

        [HttpGet]
        public IEnumerable<object> Get()
        {
            _logger.LogInformation("GET /api/payments called");
            return new[] {
                new { Id = 1, InvoiceId = 1, Amount = 120.50, Date = "2026-04-01", Method = "Credit Card" }
            };
        }
    }
}
