using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;

namespace CustomerService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CustomersController : ControllerBase
    {
        private static readonly ILogger _logger = LoggerFactory.CreateLogger<CustomersController>();

        [HttpGet]
        public IEnumerable<object> Get()
        {
            _logger.LogInformation("GET /api/customers called");
            return new[] {
                new { Id = 1, Name = "Jane Doe", Address = "123 Main St", Email = "jane@example.com", Phone = "555-1234" }
            };
        }
    }
}
