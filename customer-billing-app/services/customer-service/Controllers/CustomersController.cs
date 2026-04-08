using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;

namespace CustomerService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CustomersController : ControllerBase
    {
        private readonly ILogger<CustomersController> _logger;

        public static readonly List<Dictionary<string, object>> Customers = new()
        {
            new() { ["id"]=1, ["name"]="Margaret Chen", ["address"]="1847 Oakwood Dr, Chicago, IL 60614", ["email"]="m.chen@email.com", ["phone"]="312-555-0147", ["accountNumber"]="ACCT-10001", ["meterNumber"]="MTR-20001", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="4821", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=2, ["name"]="David Richardson", ["address"]="503 Industrial Pkwy, Baltimore, MD 21201", ["email"]="d.richardson@email.com", ["phone"]="410-555-0238", ["accountNumber"]="ACCT-10002", ["meterNumber"]="MTR-20002", ["serviceType"]="Commercial", ["rateClass"]="C-2", ["creditCardLast4"]="7193", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=true },
            new() { ["id"]=3, ["name"]="Sarah Kim", ["address"]="2290 Elm Street, Philadelphia, PA 19103", ["email"]="s.kim@email.com", ["phone"]="215-555-0392", ["accountNumber"]="ACCT-10003", ["meterNumber"]="MTR-20003", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="3056", ["creditCardType"]="Visa", ["autoPayEnabled"]=false },
            new() { ["id"]=4, ["name"]="James O'Brien", ["address"]="8100 Commerce Blvd, Washington, DC 20001", ["email"]="j.obrien@email.com", ["phone"]="202-555-0461", ["accountNumber"]="ACCT-10004", ["meterNumber"]="MTR-20004", ["serviceType"]="Industrial", ["rateClass"]="I-3", ["creditCardLast4"]="8417", ["creditCardType"]="Amex", ["autoPayEnabled"]=true },
            new() { ["id"]=5, ["name"]="Linda Martinez", ["address"]="315 Shore Ave, Atlantic City, NJ 08401", ["email"]="l.martinez@email.com", ["phone"]="609-555-0528", ["accountNumber"]="ACCT-10005", ["meterNumber"]="MTR-20005", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="6290", ["creditCardType"]="Discover", ["autoPayEnabled"]=true },
            new() { ["id"]=6, ["name"]="Robert Taylor", ["address"]="4422 Market St, Wilmington, DE 19801", ["email"]="r.taylor@email.com", ["phone"]="302-555-0619", ["accountNumber"]="ACCT-10006", ["meterNumber"]="MTR-20006", ["serviceType"]="Commercial", ["rateClass"]="C-1", ["creditCardLast4"]="1748", ["creditCardType"]="Visa", ["autoPayEnabled"]=false },
            new() { ["id"]=7, ["name"]="Patricia Wong", ["address"]="1105 Lake Shore Dr, Chicago, IL 60611", ["email"]="p.wong@email.com", ["phone"]="312-555-0773", ["accountNumber"]="ACCT-10007", ["meterNumber"]="MTR-20007", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="5034", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=true },
            new() { ["id"]=8, ["name"]="Michael Brown", ["address"]="6789 Factory Rd, Baltimore, MD 21224", ["email"]="m.brown@email.com", ["phone"]="410-555-0845", ["accountNumber"]="ACCT-10008", ["meterNumber"]="MTR-20008", ["serviceType"]="Industrial", ["rateClass"]="I-2", ["creditCardLast4"]="2961", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=9, ["name"]="Jennifer Davis", ["address"]="892 Walnut Ln, Philadelphia, PA 19147", ["email"]="j.davis@email.com", ["phone"]="215-555-0916", ["accountNumber"]="ACCT-10009", ["meterNumber"]="MTR-20009", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="7382", ["creditCardType"]="Amex", ["autoPayEnabled"]=false },
            new() { ["id"]=10, ["name"]="William Garcia", ["address"]="2010 Penn Ave NW, Washington, DC 20037", ["email"]="w.garcia@email.com", ["phone"]="202-555-1047", ["accountNumber"]="ACCT-10010", ["meterNumber"]="MTR-20010", ["serviceType"]="Commercial", ["rateClass"]="C-2", ["creditCardLast4"]="4105", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=true },
            new() { ["id"]=11, ["name"]="Karen Wilson", ["address"]="567 Birch Ct, Cherry Hill, NJ 08002", ["email"]="k.wilson@email.com", ["phone"]="856-555-1138", ["accountNumber"]="ACCT-10011", ["meterNumber"]="MTR-20011", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="8573", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=12, ["name"]="Thomas Anderson", ["address"]="3341 Warehouse Dist, Chicago, IL 60607", ["email"]="t.anderson@email.com", ["phone"]="312-555-1229", ["accountNumber"]="ACCT-10012", ["meterNumber"]="MTR-20012", ["serviceType"]="Commercial", ["rateClass"]="C-3", ["creditCardLast4"]="6241", ["creditCardType"]="Discover", ["autoPayEnabled"]=false },
            new() { ["id"]=13, ["name"]="Nancy Thompson", ["address"]="1450 Rittenhouse Sq, Philadelphia, PA 19103", ["email"]="n.thompson@email.com", ["phone"]="215-555-1330", ["accountNumber"]="ACCT-10013", ["meterNumber"]="MTR-20013", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="9164", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=14, ["name"]="Charles Lee", ["address"]="7800 Steel Mill Rd, Baltimore, MD 21230", ["email"]="c.lee@email.com", ["phone"]="410-555-1421", ["accountNumber"]="ACCT-10014", ["meterNumber"]="MTR-20014", ["serviceType"]="Industrial", ["rateClass"]="I-3", ["creditCardLast4"]="2087", ["creditCardType"]="Amex", ["autoPayEnabled"]=true },
            new() { ["id"]=15, ["name"]="Jessica Moore", ["address"]="224 Boardwalk, Atlantic City, NJ 08401", ["email"]="j.moore@email.com", ["phone"]="609-555-1512", ["accountNumber"]="ACCT-10015", ["meterNumber"]="MTR-20015", ["serviceType"]="Commercial", ["rateClass"]="C-1", ["creditCardLast4"]="3756", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=false },
            new() { ["id"]=16, ["name"]="Daniel Harris", ["address"]="9012 Georgetown Rd, Washington, DC 20007", ["email"]="d.harris@email.com", ["phone"]="202-555-1603", ["accountNumber"]="ACCT-10016", ["meterNumber"]="MTR-20016", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="5498", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=17, ["name"]="Emily Clark", ["address"]="1780 Wicker Park, Chicago, IL 60622", ["email"]="e.clark@email.com", ["phone"]="312-555-1794", ["accountNumber"]="ACCT-10017", ["meterNumber"]="MTR-20017", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="8620", ["creditCardType"]="Discover", ["autoPayEnabled"]=true },
            new() { ["id"]=18, ["name"]="Andrew Robinson", ["address"]="450 Brandywine Blvd, Wilmington, DE 19802", ["email"]="a.robinson@email.com", ["phone"]="302-555-1885", ["accountNumber"]="ACCT-10018", ["meterNumber"]="MTR-20018", ["serviceType"]="Commercial", ["rateClass"]="C-2", ["creditCardLast4"]="1379", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=19, ["name"]="Michelle Lewis", ["address"]="3025 Canton St, Baltimore, MD 21224", ["email"]="m.lewis@email.com", ["phone"]="410-555-1976", ["accountNumber"]="ACCT-10019", ["meterNumber"]="MTR-20019", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="4932", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=false },
            new() { ["id"]=20, ["name"]="Kevin Walker", ["address"]="5567 Spring Garden, Philadelphia, PA 19123", ["email"]="k.walker@email.com", ["phone"]="215-555-2067", ["accountNumber"]="ACCT-10020", ["meterNumber"]="MTR-20020", ["serviceType"]="Industrial", ["rateClass"]="I-1", ["creditCardLast4"]="7845", ["creditCardType"]="Amex", ["autoPayEnabled"]=true },
            new() { ["id"]=21, ["name"]="Amanda Young", ["address"]="188 Dupont Circle, Washington, DC 20036", ["email"]="a.young@email.com", ["phone"]="202-555-2158", ["accountNumber"]="ACCT-10021", ["meterNumber"]="MTR-20021", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="2516", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=22, ["name"]="Christopher Hall", ["address"]="6320 Navy Pier Dr, Chicago, IL 60611", ["email"]="c.hall@email.com", ["phone"]="312-555-2249", ["accountNumber"]="ACCT-10022", ["meterNumber"]="MTR-20022", ["serviceType"]="Commercial", ["rateClass"]="C-1", ["creditCardLast4"]="6083", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=false },
            new() { ["id"]=23, ["name"]="Stephanie Allen", ["address"]="741 Margate Ave, Ventnor City, NJ 08406", ["email"]="s.allen@email.com", ["phone"]="609-555-2340", ["accountNumber"]="ACCT-10023", ["meterNumber"]="MTR-20023", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="9471", ["creditCardType"]="Discover", ["autoPayEnabled"]=true },
            new() { ["id"]=24, ["name"]="Brian Scott", ["address"]="2100 N Charles St, Baltimore, MD 21218", ["email"]="b.scott@email.com", ["phone"]="410-555-2431", ["accountNumber"]="ACCT-10024", ["meterNumber"]="MTR-20024", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="3208", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=25, ["name"]="Rachel Green", ["address"]="980 Chestnut Hill, Philadelphia, PA 19118", ["email"]="r.green@email.com", ["phone"]="215-555-2522", ["accountNumber"]="ACCT-10025", ["meterNumber"]="MTR-20025", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="5764", ["creditCardType"]="Amex", ["autoPayEnabled"]=false },
            new() { ["id"]=26, ["name"]="Jason King", ["address"]="4455 H Street NE, Washington, DC 20002", ["email"]="j.king@email.com", ["phone"]="202-555-2613", ["accountNumber"]="ACCT-10026", ["meterNumber"]="MTR-20026", ["serviceType"]="Commercial", ["rateClass"]="C-3", ["creditCardLast4"]="1697", ["creditCardType"]="Visa", ["autoPayEnabled"]=true },
            new() { ["id"]=27, ["name"]="Laura Wright", ["address"]="1330 Logan Sq, Chicago, IL 60607", ["email"]="l.wright@email.com", ["phone"]="312-555-2704", ["accountNumber"]="ACCT-10027", ["meterNumber"]="MTR-20027", ["serviceType"]="Residential", ["rateClass"]="R-1", ["creditCardLast4"]="8340", ["creditCardType"]="Mastercard", ["autoPayEnabled"]=true },
            new() { ["id"]=28, ["name"]="Steven Baker", ["address"]="705 Kirkwood Hwy, Wilmington, DE 19805", ["email"]="s.baker@email.com", ["phone"]="302-555-2895", ["accountNumber"]="ACCT-10028", ["meterNumber"]="MTR-20028", ["serviceType"]="Industrial", ["rateClass"]="I-2", ["creditCardLast4"]="4152", ["creditCardType"]="Discover", ["autoPayEnabled"]=true },
            new() { ["id"]=29, ["name"]="Maria Rodriguez", ["address"]="2678 Federal Hill, Baltimore, MD 21230", ["email"]="m.rodriguez@email.com", ["phone"]="410-555-2986", ["accountNumber"]="ACCT-10029", ["meterNumber"]="MTR-20029", ["serviceType"]="Residential", ["rateClass"]="R-2", ["creditCardLast4"]="7529", ["creditCardType"]="Visa", ["autoPayEnabled"]=false },
            new() { ["id"]=30, ["name"]="Gregory Nguyen", ["address"]="5100 Plant Rd, Chester, PA 19013", ["email"]="g.nguyen@email.com", ["phone"]="610-555-3077", ["accountNumber"]="ACCT-10030", ["meterNumber"]="MTR-20030", ["serviceType"]="Industrial", ["rateClass"]="I-3", ["creditCardLast4"]="0863", ["creditCardType"]="Amex", ["autoPayEnabled"]=true }
        };

        public CustomersController(ILogger<CustomersController> logger)
        {
            _logger = logger;
        }

        [HttpGet]
        public IActionResult Get()
        {
            _logger.LogInformation("GET /api/customers - returning {Count} customers", Customers.Count);
            return Ok(Customers);
        }

        [HttpGet("{id}")]
        public IActionResult GetById(int id)
        {
            _logger.LogInformation("GET /api/customers/{Id}", id);
            var customer = Customers.Find(c => (int)c["id"] == id);
            if (customer == null) return NotFound(new { error = "Customer not found", id });
            return Ok(customer);
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { Status = "Healthy", Service = "CustomerService" });
        }
    }
}
