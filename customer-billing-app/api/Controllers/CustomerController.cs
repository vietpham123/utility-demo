using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace CustomerBillingApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CustomerController : ControllerBase
    {
        [HttpGet]
        public IEnumerable<object> Get()
        {
            return new[] {
                new { Id = 1, Name = "Jane Doe", Address = "123 Main St", Email = "jane@example.com", Phone = "555-1234" }
            };
        }
    }
}
