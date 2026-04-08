using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;

namespace InvoiceService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InvoicesController : ControllerBase
    {
        private static readonly ILogger _logger = LoggerFactory.CreateLogger<InvoicesController>();

        [HttpGet]
        public IEnumerable<object> Get()
        {
            _logger.LogInformation("GET /api/invoices called");
            return new[] {
                new { Id = 1, CustomerId = 1, Amount = 120.50, DueDate = "2026-05-01", Status = "Unpaid" }
            };
        }
    }
}
