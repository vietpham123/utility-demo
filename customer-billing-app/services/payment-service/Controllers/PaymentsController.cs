using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;

namespace PaymentService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PaymentsController : ControllerBase
    {
        private readonly ILogger<PaymentsController> _logger;
        private static readonly Random _rng = new(99);
        private static readonly object _lock = new();
        private static readonly List<Dictionary<string, object>> _payments = new();
        private static bool _initialized = false;
        private static int _nextId = 5001;

        private static readonly string[] _methods = { "Credit Card", "Bank Transfer", "Auto Pay", "Check", "ACH Direct" };
        private static readonly string[] _prefixes = { "PAY-CC", "PAY-BT", "PAY-AP", "PAY-CK", "PAY-ACH" };

        private static readonly (int id, string acct, bool autopay)[] _customers = new[]
        {
            (1,"ACCT-10001",true),(2,"ACCT-10002",true),(3,"ACCT-10003",false),(4,"ACCT-10004",true),
            (5,"ACCT-10005",true),(6,"ACCT-10006",false),(7,"ACCT-10007",true),(8,"ACCT-10008",true),
            (9,"ACCT-10009",false),(10,"ACCT-10010",true),(11,"ACCT-10011",true),(12,"ACCT-10012",false),
            (13,"ACCT-10013",true),(14,"ACCT-10014",true),(15,"ACCT-10015",false),(16,"ACCT-10016",true),
            (17,"ACCT-10017",true),(18,"ACCT-10018",true),(19,"ACCT-10019",false),(20,"ACCT-10020",true),
            (21,"ACCT-10021",true),(22,"ACCT-10022",false),(23,"ACCT-10023",true),(24,"ACCT-10024",true),
            (25,"ACCT-10025",false),(26,"ACCT-10026",true),(27,"ACCT-10027",true),(28,"ACCT-10028",true),
            (29,"ACCT-10029",false),(30,"ACCT-10030",true)
        };

        private static void EnsureInitialized()
        {
            if (_initialized) return;
            lock (_lock)
            {
                if (_initialized) return;
                var now = DateTime.UtcNow;
                var statuses = new[] { "Completed", "Completed", "Completed", "Completed", "Pending", "Partial", "Failed" };

                // Generate payment history: ~4 payments per customer for past billing periods
                for (int monthsAgo = 5; monthsAgo >= 1; monthsAgo--)
                {
                    var baseDate = new DateTime(now.Year, now.Month, 1).AddMonths(-monthsAgo);
                    int invoiceIdBase = 1001 + (5 - monthsAgo) * 30;

                    foreach (var c in _customers)
                    {
                        if (_rng.NextDouble() < 0.15) continue; // some customers skip a payment
                        int invoiceId = invoiceIdBase + (c.id - 1);
                        int methodIdx = c.autopay ? 2 : _rng.Next(_methods.Length);
                        string status = monthsAgo >= 2 ? "Completed" : statuses[_rng.Next(statuses.Length)];
                        double amount = c.id <= 10 ? 80 + _rng.Next(200) + _rng.NextDouble() * 100 :
                                        c.id <= 20 ? 100 + _rng.Next(500) + _rng.NextDouble() * 100 :
                                        150 + _rng.Next(800) + _rng.NextDouble() * 100;
                        amount = Math.Round(amount, 2);
                        if (status == "Partial") amount = Math.Round(amount * 0.5, 2);

                        int payDay = Math.Min(10 + _rng.Next(15), 28);
                        var payDate = new DateTime(baseDate.Year, baseDate.Month, payDay).AddMonths(1);

                        _payments.Add(new Dictionary<string, object>
                        {
                            ["id"] = _nextId++,
                            ["invoiceId"] = invoiceId,
                            ["customerId"] = c.id,
                            ["accountNumber"] = c.acct,
                            ["amount"] = amount,
                            ["paymentDate"] = payDate.ToString("yyyy-MM-dd"),
                            ["method"] = _methods[methodIdx],
                            ["confirmationNumber"] = $"{_prefixes[methodIdx]}-{_rng.Next(10000, 99999)}",
                            ["status"] = status
                        });
                    }
                }
                _initialized = true;
            }
        }

        public PaymentsController(ILogger<PaymentsController> logger)
        {
            _logger = logger;
            EnsureInitialized();
        }

        [HttpGet]
        public IActionResult Get([FromQuery] int? customerId)
        {
            if (customerId.HasValue)
            {
                var filtered = _payments.Where(p => (int)p["customerId"] == customerId.Value).ToList();
                _logger.LogInformation("GET /api/payments?customerId={CustId} - returning {Count}", customerId, filtered.Count);
                return Ok(filtered);
            }
            _logger.LogInformation("GET /api/payments - returning {Count} payments", _payments.Count);
            return Ok(_payments);
        }

        [HttpGet("{id}")]
        public IActionResult GetById(int id)
        {
            _logger.LogInformation("GET /api/payments/{Id}", id);
            var payment = _payments.Find(p => (int)p["id"] == id);
            if (payment == null) return NotFound();
            return Ok(payment);
        }

        [HttpPost]
        public IActionResult Create([FromBody] Dictionary<string, object> payment)
        {
            lock (_lock)
            {
                payment["id"] = _nextId++;
                _payments.Add(payment);
            }
            _logger.LogInformation("POST /api/payments - created payment {Id} for account {Acct}", payment["id"], payment.GetValueOrDefault("accountNumber"));
            return CreatedAtAction(nameof(GetById), new { id = payment["id"] }, payment);
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new { Status = "Healthy", Service = "PaymentService", PaymentCount = _payments.Count });
        }
    }
}
