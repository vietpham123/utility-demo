const express = require('express');
const app = express();
app.use(express.json());

const outages = [
  { id: '1', location: 'Downtown', startTime: '2026-04-01T10:00:00Z', endTime: null, status: 'Active', affectedCustomers: 120 }
];

const usage = [
  { id: '1', customerId: '1', timestamp: '2026-04-01T09:00:00Z', usageKWh: 15.2 }
];

app.get('/api/outages', (req, res) => res.json(outages));
app.post('/api/outages', (req, res) => {
  outages.push(req.body);
  res.status(201).json(req.body);
});

app.get('/api/usage', (req, res) => res.json(usage));
app.post('/api/usage', (req, res) => {
  usage.push(req.body);
  res.status(201).json(req.body);
});

const port = process.env.PORT || 3001;
app.listen(port, () => console.log(`Outage Analytics API running on port ${port}`));
