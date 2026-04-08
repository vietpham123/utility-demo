using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace CustomerBillingApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InvoiceController : ControllerBase
    {
        [HttpGet]
        public IEnumerable<object> Get()
        {
            return new[] {
                new { Id = 1, CustomerId = 1, Amount = 120.50, DueDate = "2026-05-01", Status = "Unpaid" }
            };
        }
    }
}
