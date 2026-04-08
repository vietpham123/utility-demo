using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;

namespace InvoiceService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InvoicesController : ControllerBase
    {
        private readonly ILogger<InvoicesController> _logger;
        private static readonly Random _rng = new(42);
        private static readonly object _lock = new();
        private static readonly List<Dictionary<string, object>> _invoices = new();
        private static bool _initialized = false;
        private static int _nextId = 1001;

        private static readonly Dictionary<string, double[]> _rateMap = new()
        {
            ["R-1"] = new[] { 0.12, 28.50 },
            ["R-2"] = new[] { 0.13, 32.00 },
            ["C-1"] = new[] { 0.10, 55.00 },
            ["C-2"] = new[] { 0.09, 75.00 },
            ["C-3"] = new[] { 0.085, 95.00 },
            ["I-1"] = new[] { 0.075, 180.00 },
            ["I-2"] = new[] { 0.07, 250.00 },
            ["I-3"] = new[] { 0.065, 320.00 }
        };

        private static readonly (int id, string acct, string rate, string svcType)[] _customers = new[]
        {
            (1,"ACCT-10001","R-1","Residential"),(2,"ACCT-10002","C-2","Commercial"),(3,"ACCT-10003","R-1","Residential"),
            (4,"ACCT-10004","I-3","Industrial"),(5,"ACCT-10005","R-2","Residential"),(6,"ACCT-10006","C-1","Commercial"),
            (7,"ACCT-10007","R-1","Residential"),(8,"ACCT-10008","I-2","Industrial"),(9,"ACCT-10009","R-2","Residential"),
            (10,"ACCT-10010","C-2","Commercial"),(11,"ACCT-10011","R-1","Residential"),(12,"ACCT-10012","C-3","Commercial"),
            (13,"ACCT-10013","R-1","Residential"),(14,"ACCT-10014","I-3","Industrial"),(15,"ACCT-10015","C-1","Commercial"),
            (16,"ACCT-10016","R-2","Residential"),(17,"ACCT-10017","R-1","Residential"),(18,"ACCT-10018","C-2","Commercial"),
            (19,"ACCT-10019","R-1","Residential"),(20,"ACCT-10020","I-1","Industrial"),(21,"ACCT-10021","R-2","Residential"),
            (22,"ACCT-10022","C-1","Commercial"),(23,"ACCT-10023","R-1","Residential"),(24,"ACCT-10024","R-2","Residential"),
            (25,"ACCT-10025","R-1","Residential"),(26,"ACCT-10026","C-3","Commercial"),(27,"ACCT-10027","R-1","Residential"),
            (28,"ACCT-10028","I-2","Industrial"),(29,"ACCT-10029","R-2","Residential"),(30,"ACCT-10030","I-3","Industrial")
        };

        private static void EnsureInitialized()
        {
            if (_initialized) return;
            lock (_lock)
            {
                if (_initialized) return;
                var now = DateTime.UtcNow;
                var statuses = new[] { "Paid", "Paid", "Paid", "Unpaid", "Overdue" };

                for (int monthsAgo = 5; monthsAgo >= 0; monthsAgo--)
                {
                    var periodStart = new DateTime(now.Year, now.Month, 1).AddMonths(-monthsAgo);
                    var periodEnd = periodStart.AddMonths(1).AddDays(-1);
                    var dueDate = periodEnd.AddDays(25);
                    var invoiceDate = periodEnd.AddDays(1);
                    var status = monthsAgo >= 2 ? "Paid" : (monthsAgo == 1 ? statuses[_rng.Next(statuses.Length)] : "Unpaid");

                    foreach (var c in _customers)
                    {
                        var rates = _rateMap[c.rate];
                        double baseUsage = c.svcType switch
                        {
                            "Residential" => 600 + _rng.Next(400),
                            "Commercial" => 2000 + _rng.Next(2000),
                            "Industrial" => 8000 + _rng.Next(10000),
                            _ => 500
                        };
                        double seasonFactor = Math.Abs(periodStart.Month - 7) < 3 ? 1.3 : (periodStart.Month < 4 || periodStart.Month > 10 ? 1.2 : 1.0);
                        double usage = Math.Round(baseUsage * seasonFactor + _rng.Next(-100, 100), 1);
                        double energyCharge = Math.Round(usage * rates[0], 2);
                        double deliveryCharge = rates[1];
                        double taxesAndFees = Math.Round((energyCharge + deliveryCharge) * 0.11, 2);
                        double total = Math.Round(energyCharge + deliveryCharge + taxesAndFees, 2);
                        string invStatus = monthsAgo == 0 ? "Unpaid" : (monthsAgo == 1 && _rng.NextDouble() > 0.6 ? "Overdue" : "Paid");

                        _invoices.Add(new Dictionary<string, object>
                        {
                            ["id"] = _nextId++,
                            ["customerId"] = c.id,
                            ["accountNumber"] = c.acct,
                            ["billingPeriodStart"] = periodStart.ToString("yyyy-MM-dd"),
                            ["billingPeriodEnd"] = periodEnd.ToString("yyyy-MM-dd"),
                            ["usageKWh"] = usage,
                            ["ratePerKWh"] = rates[0],
                            ["energyCharge"] = energyCharge,
                            ["deliveryCharge"] = deliveryCharge,
                            ["taxesAndFees"] = taxesAndFees,
                            ["totalAmount"] = total,
                            ["dueDate"] = dueDate.ToString("yyyy-MM-dd"),
                            ["status"] = invStatus,
                            ["invoiceDate"] = invoiceDate.ToString("yyyy-MM-dd")
                        });
                    }
                }
                _initialized = true;
            }
        }

        public InvoicesController(ILogger<InvoicesController> logger)
        {
            _logger = logger;
            EnsureInitialized();
        }

        [HttpGet]
        public IActionResult Get([FromQuery] int? customerId)
        {
            if (customerId.HasValue)
            {
                var filtered = _invoices.Where(i => (int)i["customerId"] == customerId.Value).ToList();
                _logger.LogInformation("GET /api/invoices?customerId={CustId} - returning {Count}", customerId, filtered.Count);
                return Ok(filtered);
            }
            _logger.LogInformation("GET /api/invoices - returning {Count} invoices", _invoices.Count);
            return Ok(_invoices);
        }

        [HttpGet("{id}")]
        public IActionResult GetById(int id)
        {
            _logger.LogInformation("GET /api/invoices/{Id}", id);
            var invoice = _invoices.Find(i => (int)i["id"] == id);
            if (invoice == null) return NotFound();
            return Ok(invoice);
        }

        [HttpPost]
        public IActionResult Create([FromBody] Dictionary<string, object> invoice)
        {
            lock (_lock)
            {
                invoice["id"] = _nextId++;
                _invoices.Add(invoice);
            }
            _logger.LogInformation("POST /api/invoices - created invoice {Id}", invoice["id"]);
            return CreatedAtAction(nameof(GetById), new { id = invoice["id"] }, invoice);
        }

        [HttpPatch("{id}/status")]
        public IActionResult UpdateStatus(int id, [FromBody] Dictionary<string, string> body)
        {
            var invoice = _invoices.Find(i => (int)i["id"] == id);
            if (invoice == null) return NotFound();
            if (body.ContainsKey("status"))
            {
                invoice["status"] = body["status"];
                _logger.LogInformation("PATCH /api/invoices/{Id}/status - updated to {Status}", id, body["status"]);
            }
            return Ok(invoice);
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { Status = "Healthy", Service = "InvoiceService", InvoiceCount = _invoices.Count });
        }
    }
}
