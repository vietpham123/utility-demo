using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace CustomerBillingApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PaymentController : ControllerBase
    {
        [HttpGet]
        public IEnumerable<object> Get()
        {
            return new[] {
                new { Id = 1, InvoiceId = 1, Amount = 120.50, Date = "2026-04-01", Method = "Credit Card" }
            };
        }
    }
}
