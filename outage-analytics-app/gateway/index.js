const express = require('express');
const axios = require('axios');
const logger = require('./logger');
const app = express();
app.use(express.json());

const OUTAGE_URL = process.env.OUTAGE_SERVICE_URL || 'http://outage-service:3000';
const USAGE_URL = process.env.USAGE_SERVICE_URL || 'http://usage-service:3000';
const SCADA_URL = process.env.SCADA_SERVICE_URL || 'http://scada-service';
const METER_URL = process.env.METER_SERVICE_URL || 'http://meter-data-service:8080';
const GRID_URL = process.env.GRID_SERVICE_URL || 'http://grid-topology-service:3000';
const RELIABILITY_URL = process.env.RELIABILITY_SERVICE_URL || 'http://reliability-service:5000';
const FORECAST_URL = process.env.FORECAST_SERVICE_URL || 'http://demand-forecast-service:3000';
const CREW_URL = process.env.CREW_SERVICE_URL || 'http://crew-dispatch-service:3001';
const NOTIFICATION_URL = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:5001';
const WEATHER_URL = process.env.WEATHER_SERVICE_URL || 'http://weather-service:8080';

// ============================================================
// Request logging middleware — debug/info/error for every request
// ============================================================
app.use((req, res, next) => {
  const start = Date.now();
  logger.debug('Incoming request', { method: req.method, path: req.path, query: req.query, ip: req.ip });

  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = { method: req.method, path: req.path, status: res.statusCode, durationMs: duration };
    if (res.statusCode >= 500) {
      logger.error('Request failed with server error', logData);
    } else if (res.statusCode >= 400) {
      logger.warn('Request completed with client error', logData);
    } else if (duration > 5000) {
      logger.warn('Slow request detected', { ...logData, threshold: '5000ms' });
    } else {
      logger.info('Request completed', logData);
    }
  });

  // ~2% chance: sporadic gateway timeout simulation
  if (Math.random() < 0.02 && req.path !== '/api/health' && req.path !== '/api/simulate/cycle') {
    const delayMs = 3000 + Math.floor(Math.random() * 5000);
    logger.warn('Simulating gateway slowdown', { path: req.path, delayMs });
    setTimeout(() => next(), delayMs);
    return;
  }

  next();
});

function proxy(targetUrl) {
  return async (req, res) => {
    const url = `${targetUrl}${req.originalUrl}`;
    logger.info(`Gateway proxy: ${req.method} ${req.originalUrl}`);
    try {
      const opts = { method: req.method, url, timeout: 8000 };
      if (['POST', 'PUT', 'PATCH'].includes(req.method)) opts.data = req.body;
      if (Object.keys(req.query).length) opts.params = req.query;
      const { data } = await axios(opts);
      res.json(data);
    } catch (err) {
      const status = err.response ? err.response.status : 502;
      logger.error(`Gateway error: ${req.originalUrl}`, { error: err.message, status });
      res.status(status).json({ error: `Service unavailable: ${err.message}` });
    }
  };
}

// Outage routes
app.get('/api/outages', proxy(OUTAGE_URL));
app.get('/api/outages/active', proxy(OUTAGE_URL));
app.get('/api/outages/stats/summary', proxy(OUTAGE_URL));
app.get('/api/outages/:id', proxy(OUTAGE_URL));
app.post('/api/outages', proxy(OUTAGE_URL));

// Usage routes
app.get('/api/usage', proxy(USAGE_URL));
app.get('/api/usage/summary', proxy(USAGE_URL));
app.get('/api/usage/customer/:customerId', proxy(USAGE_URL));

// SCADA routes
app.get('/api/scada/sensors', proxy(SCADA_URL));
app.get('/api/scada/readings/latest', proxy(SCADA_URL));
app.get('/api/scada/readings/history', proxy(SCADA_URL));
app.get('/api/scada/readings/equipment/:type/:id', proxy(SCADA_URL));
app.get('/api/scada/alerts', proxy(SCADA_URL));
app.get('/api/scada/alerts/active', proxy(SCADA_URL));
app.get('/api/scada/summary', proxy(SCADA_URL));
app.post('/api/scada/simulate', proxy(SCADA_URL));

// Meter Data (MDMS) routes
app.get('/api/meter-data/readings', proxy(METER_URL));
app.get('/api/meter-data/readings/:meterId', proxy(METER_URL));
app.get('/api/meter-data/readings/customer/:customerId', proxy(METER_URL));
app.get('/api/meter-data/anomalies', proxy(METER_URL));
app.get('/api/meter-data/meters', proxy(METER_URL));
app.get('/api/meter-data/summary', proxy(METER_URL));
app.post('/api/meter-data/simulate', proxy(METER_URL));

// Grid Topology routes
app.get('/api/grid/substations', proxy(GRID_URL));
app.get('/api/grid/substations/:id', proxy(GRID_URL));
app.get('/api/grid/feeders', proxy(GRID_URL));
app.get('/api/grid/feeders/substation/:substationId', proxy(GRID_URL));
app.get('/api/grid/transformers', proxy(GRID_URL));
app.get('/api/grid/service-points', proxy(GRID_URL));
app.get('/api/grid/topology', proxy(GRID_URL));
app.get('/api/grid/affected-customers/:type/:id', proxy(GRID_URL));
app.get('/api/grid/stats', proxy(GRID_URL));

// Reliability indices routes
app.get('/api/reliability/indices', proxy(RELIABILITY_URL));
app.get('/api/reliability/history', proxy(RELIABILITY_URL));
app.get('/api/reliability/trends', proxy(RELIABILITY_URL));
app.get('/api/reliability/events', proxy(RELIABILITY_URL));

// Demand Forecast routes
app.get('/api/forecast/current', proxy(FORECAST_URL));
app.get('/api/forecast/hourly', proxy(FORECAST_URL));
app.get('/api/forecast/peak-demand', proxy(FORECAST_URL));
app.get('/api/forecast/summary', proxy(FORECAST_URL));
app.get('/api/forecast/areas', proxy(FORECAST_URL));

// Crew Dispatch routes
app.get('/api/crew/crews', proxy(CREW_URL));
app.get('/api/crew/crews/available', proxy(CREW_URL));
app.get('/api/crew/dispatches', proxy(CREW_URL));
app.get('/api/crew/dispatches/active', proxy(CREW_URL));
app.get('/api/crew/dispatches/:id', proxy(CREW_URL));
app.get('/api/crew/stats', proxy(CREW_URL));
app.post('/api/crew/simulate', proxy(CREW_URL));

// Customer Notification routes
app.get('/api/notifications/log', proxy(NOTIFICATION_URL));
app.get('/api/notifications/stats', proxy(NOTIFICATION_URL));
app.get('/api/notifications/customers', proxy(NOTIFICATION_URL));
app.post('/api/notifications/simulate', proxy(NOTIFICATION_URL));

// Weather Correlation routes (Go + gRPC)
app.get('/api/weather/conditions', proxy(WEATHER_URL));
app.get('/api/weather/region/:region', proxy(WEATHER_URL));
app.get('/api/weather/forecast', proxy(WEATHER_URL));
app.get('/api/weather/alerts', proxy(WEATHER_URL));
app.get('/api/weather/correlations', proxy(WEATHER_URL));
app.get('/api/weather/summary', proxy(WEATHER_URL));
app.post('/api/weather/simulate', proxy(WEATHER_URL));
app.post('/api/weather/correlate', proxy(WEATHER_URL));

// ============================================================
// Simulation Orchestrator — creates end-to-end Dynatrace PurePaths
// Gateway → HTTP calls to all services → each service writes DB/Kafka/Redis
// Dynatrace OneAgent auto-instruments HTTP, Kafka, DB, Redis spans
// ============================================================
app.post('/api/simulate/cycle', async (req, res) => {
  const cycleStart = Date.now();
  logger.info('POST /api/simulate/cycle - orchestrating simulation cycle');
  const results = {};

  // Wave 1: Data generators (parallel) — SCADA, Meter, Forecast, Weather
  const wave1 = await Promise.allSettled([
    axios.post(`${SCADA_URL}/api/scada/simulate`, {}, { timeout: 10000 })
      .then(r => { results.scada = r.data; })
      .catch(err => { results.scada = { error: err.message }; }),
    axios.post(`${METER_URL}/api/meter-data/simulate`, {}, { timeout: 10000 })
      .then(r => { results.meter = r.data; })
      .catch(err => { results.meter = { error: err.message }; }),
    axios.post(`${FORECAST_URL}/api/forecast/simulate`, {}, { timeout: 10000 })
      .then(r => { results.forecast = r.data; })
      .catch(err => { results.forecast = { error: err.message }; }),
    axios.post(`${WEATHER_URL}/api/weather/simulate`, {}, { timeout: 10000 })
      .then(r => { results.weather = r.data; })
      .catch(err => { results.weather = { error: err.message }; })
  ]);

  // Wave 2: Event processors (parallel) — Outage, Usage
  const wave2 = await Promise.allSettled([
    axios.post(`${OUTAGE_URL}/api/outages/simulate`, {}, { timeout: 10000 })
      .then(r => { results.outage = r.data; })
      .catch(err => { results.outage = { error: err.message }; }),
    axios.post(`${USAGE_URL}/api/usage/simulate`, {}, { timeout: 10000 })
      .then(r => { results.usage = r.data; })
      .catch(err => { results.usage = { error: err.message }; })
  ]);

  // Wave 3: Analytics — Reliability calculation (depends on outage data)
  await axios.post(`${RELIABILITY_URL}/api/reliability/calculate`, {}, { timeout: 10000 })
    .then(r => { results.reliability = r.data; })
    .catch(err => { results.reliability = { error: err.message }; });

  // Wave 4: Operations (parallel) — Crew Dispatch + Customer Notifications (depends on outage data)
  const wave4 = await Promise.allSettled([
    axios.post(`${CREW_URL}/api/crew/simulate`, {}, { timeout: 10000 })
      .then(r => { results.crew = r.data; })
      .catch(err => { results.crew = { error: err.message }; }),
    axios.post(`${NOTIFICATION_URL}/api/notifications/simulate`, {}, { timeout: 10000 })
      .then(r => { results.notifications = r.data; })
      .catch(err => { results.notifications = { error: err.message }; })
  ]);

  const durationMs = Date.now() - cycleStart;
  logger.info('Simulation cycle complete', { durationMs, services: Object.keys(results).length });
  res.json({ status: 'Cycle complete', durationMs, results });
});

// Aggregated dashboard endpoint
app.get('/api/dashboard', async (req, res) => {
  logger.info('GET /api/dashboard - aggregating all services');
  const fetches = {
    outages: axios.get(`${OUTAGE_URL}/api/outages/stats/summary`).then(r => r.data).catch(() => null),
    usage: axios.get(`${USAGE_URL}/api/usage/summary`).then(r => r.data).catch(() => null),
    scada: axios.get(`${SCADA_URL}/api/scada/summary`).then(r => r.data).catch(() => null),
    meterData: axios.get(`${METER_URL}/api/meter-data/summary`).then(r => r.data).catch(() => null),
    grid: axios.get(`${GRID_URL}/api/grid/stats`).then(r => r.data).catch(() => null),
    reliability: axios.get(`${RELIABILITY_URL}/api/reliability/indices`).then(r => r.data).catch(() => null),
    forecast: axios.get(`${FORECAST_URL}/api/forecast/summary`).then(r => r.data).catch(() => null),
    crewDispatch: axios.get(`${CREW_URL}/api/crew/stats`).then(r => r.data).catch(() => null),
    notifications: axios.get(`${NOTIFICATION_URL}/api/notifications/stats`).then(r => r.data).catch(() => null),
    weather: axios.get(`${WEATHER_URL}/api/weather/summary`).then(r => r.data).catch(() => null)
  };
  const results = {};
  for (const [key, promise] of Object.entries(fetches)) {
    results[key] = await promise;
  }
  res.json(results);
});

// Health check for all services
app.get('/api/health', async (req, res) => {
  const checks = [
    { name: 'outage-service', url: `${OUTAGE_URL}/api/outages/health` },
    { name: 'usage-service', url: `${USAGE_URL}/api/usage/health` },
    { name: 'scada-service', url: `${SCADA_URL}/api/scada/health` },
    { name: 'meter-data-service', url: `${METER_URL}/api/meter-data/health` },
    { name: 'grid-topology-service', url: `${GRID_URL}/api/grid/health` },
    { name: 'reliability-service', url: `${RELIABILITY_URL}/api/reliability/health` },
    { name: 'demand-forecast-service', url: `${FORECAST_URL}/api/forecast/health` },
    { name: 'crew-dispatch-service', url: `${CREW_URL}/api/crew/health` },
    { name: 'notification-service', url: `${NOTIFICATION_URL}/api/notifications/health` },
    { name: 'weather-service', url: `${WEATHER_URL}/api/weather/health` }
  ];
  const results = await Promise.all(checks.map(async c => {
    try {
      const { data } = await axios.get(c.url, { timeout: 3000 });
      return { ...c, status: 'Healthy', details: data };
    } catch (err) {
      return { ...c, status: 'Unhealthy', error: err.message };
    }
  }));
  const allHealthy = results.every(r => r.status === 'Healthy');
  res.status(allHealthy ? 200 : 207).json({
    status: allHealthy ? 'Healthy' : 'Degraded',
    service: 'AnalyticsGateway',
    services: results
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  logger.info(`Analytics Gateway running on port ${port}`);

  // Periodic simulation trigger — calls own endpoint via HTTP so Dynatrace
  // creates a proper PurePath with the inbound request as the root span
  const SIMULATE_INTERVAL = parseInt(process.env.SIMULATE_INTERVAL || '15000');
  setTimeout(() => {
    logger.info(`Starting simulation orchestrator (interval: ${SIMULATE_INTERVAL}ms)`);
    setInterval(() => {
      axios.post(`http://localhost:${port}/api/simulate/cycle`, {}, { timeout: 30000 })
        .then(r => logger.info('Simulation cycle triggered', { durationMs: r.data.durationMs }))
        .catch(err => logger.warn('Simulation cycle failed', { error: err.message }));
    }, SIMULATE_INTERVAL);
  }, 30000); // Wait 30s for services to initialize
});
