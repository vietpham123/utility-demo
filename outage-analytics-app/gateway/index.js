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
// ENHANCED: 5-wave pipeline with data passing between waves
// Wave 1 (parallel): SCADA + Weather generators → produce telemetry
// Wave 2 (sequential): Weather correlation → enriches with SCADA context
// Wave 3 (parallel): Outage + Usage + Forecast + Meter data processors
// Wave 4 (sequential): Reliability calculation → depends on outage data
// Wave 5 (parallel → sequential): Crew dispatch → then notifications
// ============================================================
app.post('/api/simulate/cycle', async (req, res) => {
  const cycleStart = Date.now();
  logger.info('POST /api/simulate/cycle - orchestrating 5-wave simulation pipeline');
  const results = {};

  // Wave 1: Sensor data generators (parallel) — SCADA telemetry + Weather observations
  logger.info('Simulation Wave 1: Sensor data generation (SCADA + Weather)');
  await Promise.allSettled([
    axios.post(`${SCADA_URL}/api/scada/simulate`, {}, { timeout: 10000 })
      .then(r => { results.scada = r.data; })
      .catch(err => { results.scada = { error: err.message }; }),
    axios.post(`${WEATHER_URL}/api/weather/simulate`, {}, { timeout: 10000 })
      .then(r => { results.weather = r.data; })
      .catch(err => { results.weather = { error: err.message }; })
  ]);

  // Wave 2: Weather correlation (sequential) — correlates weather with SCADA context
  logger.info('Simulation Wave 2: Weather correlation analysis (sequential)');
  await axios.post(`${WEATHER_URL}/api/weather/correlate`, {}, { timeout: 10000 })
    .then(r => { results.weatherCorrelation = r.data; })
    .catch(err => { results.weatherCorrelation = { error: err.message }; });

  // Wave 3: Event processors (parallel) — Outage, Usage, Forecast, Meter data
  logger.info('Simulation Wave 3: Event processing (Outage + Usage + Forecast + Meter)');
  await Promise.allSettled([
    axios.post(`${OUTAGE_URL}/api/outages/simulate`, {}, { timeout: 10000 })
      .then(r => { results.outage = r.data; })
      .catch(err => { results.outage = { error: err.message }; }),
    axios.post(`${USAGE_URL}/api/usage/simulate`, {}, { timeout: 10000 })
      .then(r => { results.usage = r.data; })
      .catch(err => { results.usage = { error: err.message }; }),
    axios.post(`${FORECAST_URL}/api/forecast/simulate`, {}, { timeout: 10000 })
      .then(r => { results.forecast = r.data; })
      .catch(err => { results.forecast = { error: err.message }; }),
    axios.post(`${METER_URL}/api/meter-data/simulate`, {}, { timeout: 10000 })
      .then(r => { results.meter = r.data; })
      .catch(err => { results.meter = { error: err.message }; })
  ]);

  // Wave 4: Analytics (sequential) — Reliability calculation depends on outage data
  logger.info('Simulation Wave 4: Reliability analytics (sequential, depends on outage data)');
  await axios.post(`${RELIABILITY_URL}/api/reliability/calculate`, {}, { timeout: 10000 })
    .then(r => { results.reliability = r.data; })
    .catch(err => { results.reliability = { error: err.message }; });

  // Wave 5: Operations — Crew Dispatch first (sequential), then Notifications (depends on dispatch)
  logger.info('Simulation Wave 5a: Crew dispatch (sequential)');
  await axios.post(`${CREW_URL}/api/crew/simulate`, {}, { timeout: 10000 })
    .then(r => { results.crew = r.data; })
    .catch(err => { results.crew = { error: err.message }; });

  logger.info('Simulation Wave 5b: Customer notifications (depends on dispatch)');
  await axios.post(`${NOTIFICATION_URL}/api/notifications/simulate`, {}, { timeout: 10000 })
    .then(r => { results.notifications = r.data; })
    .catch(err => { results.notifications = { error: err.message }; });

  const durationMs = Date.now() - cycleStart;
  logger.info('Simulation cycle complete', { durationMs, waves: 5, services: Object.keys(results).length });
  res.json({ status: 'Cycle complete', durationMs, results });
});

// ============================================================
// Aggregated dashboard endpoint — PHASED sequential + parallel
// Creates rich distributed traces: infrastructure → events → analytics → ops
// ============================================================
app.get('/api/dashboard', async (req, res) => {
  const dashStart = Date.now();
  logger.info('GET /api/dashboard - phased aggregation (sequential + parallel)');
  const results = {};

  // Phase 1: Infrastructure baseline (parallel) — grid topology + SCADA telemetry
  logger.info('Dashboard Phase 1: Infrastructure data (grid + SCADA)');
  const [gridResult, scadaResult] = await Promise.allSettled([
    axios.get(`${GRID_URL}/api/grid/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${SCADA_URL}/api/scada/summary`, { timeout: 8000 }).then(r => r.data)
  ]);
  results.grid = gridResult.status === 'fulfilled' ? gridResult.value : null;
  results.scada = scadaResult.status === 'fulfilled' ? scadaResult.value : null;

  // Phase 2: Event data (parallel) — outages + weather depend on infrastructure awareness
  logger.info('Dashboard Phase 2: Event data (outages + weather)');
  const [outageResult, weatherResult] = await Promise.allSettled([
    axios.get(`${OUTAGE_URL}/api/outages/stats/summary`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${WEATHER_URL}/api/weather/summary`, { timeout: 8000 }).then(r => r.data)
  ]);
  results.outages = outageResult.status === 'fulfilled' ? outageResult.value : null;
  results.weather = weatherResult.status === 'fulfilled' ? weatherResult.value : null;

  // Phase 3: Analytics (sequential) — reliability depends on outage data, then forecast
  logger.info('Dashboard Phase 3: Analytics (reliability → forecast)');
  results.reliability = await axios.get(`${RELIABILITY_URL}/api/reliability/indices`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);
  results.forecast = await axios.get(`${FORECAST_URL}/api/forecast/summary`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  // Phase 4: Operations (parallel) — usage, meter, crew, notifications
  logger.info('Dashboard Phase 4: Operations data (usage + meter + crew + notifications)');
  const [usageResult, meterResult, crewResult, notifResult] = await Promise.allSettled([
    axios.get(`${USAGE_URL}/api/usage/summary`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${METER_URL}/api/meter-data/summary`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${CREW_URL}/api/crew/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${NOTIFICATION_URL}/api/notifications/stats`, { timeout: 8000 }).then(r => r.data)
  ]);
  results.usage = usageResult.status === 'fulfilled' ? usageResult.value : null;
  results.meterData = meterResult.status === 'fulfilled' ? meterResult.value : null;
  results.crewDispatch = crewResult.status === 'fulfilled' ? crewResult.value : null;
  results.notifications = notifResult.status === 'fulfilled' ? notifResult.value : null;

  const durationMs = Date.now() - dashStart;
  logger.info('Dashboard aggregation complete', { durationMs, phases: 4 });
  res.json(results);
});

// ============================================================
// Enriched chained endpoints — sequential service-to-service calls
// Create deep waterfall traces in Dynatrace for observability demos
// ============================================================

// Outage detail enriched: outage → crew dispatches → weather for region → grid impact
app.get('/api/outages/:id/enriched', async (req, res) => {
  const enrichStart = Date.now();
  const outageId = req.params.id;
  logger.info(`GET /api/outages/${outageId}/enriched - sequential enrichment chain`);

  // Step 1: Fetch base outage data
  logger.info('Enrichment Step 1: Fetch outage details');
  const outage = await axios.get(`${OUTAGE_URL}/api/outages/${outageId}`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);
  if (!outage) return res.status(404).json({ error: 'Outage not found' });

  // Step 2: Fetch active crew dispatches (depends on outage context)
  logger.info('Enrichment Step 2: Fetch crew dispatches');
  const dispatches = await axios.get(`${CREW_URL}/api/crew/dispatches/active`, { timeout: 8000 })
    .then(r => r.data).catch(() => []);

  // Step 3: Fetch weather for the outage region (depends on outage location)
  logger.info('Enrichment Step 3: Fetch weather for outage region');
  const region = outage.region || outage.location || 'northeast';
  const weather = await axios.get(`${WEATHER_URL}/api/weather/region/${encodeURIComponent(region)}`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  // Step 4: Fetch grid topology impact (parallel with reliability)
  logger.info('Enrichment Step 4: Grid impact + reliability (parallel)');
  const [gridResult, reliabilityResult] = await Promise.allSettled([
    axios.get(`${GRID_URL}/api/grid/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${RELIABILITY_URL}/api/reliability/indices`, { timeout: 8000 }).then(r => r.data)
  ]);

  const durationMs = Date.now() - enrichStart;
  logger.info(`Outage enrichment complete`, { outageId, durationMs, steps: 4 });
  res.json({
    outage,
    relatedDispatches: dispatches,
    weatherContext: weather,
    gridImpact: gridResult.status === 'fulfilled' ? gridResult.value : null,
    reliability: reliabilityResult.status === 'fulfilled' ? reliabilityResult.value : null,
    enrichmentDurationMs: durationMs
  });
});

// Analytics correlation: weather → outages → SCADA → reliability (full sequential chain)
app.get('/api/analytics/correlation', async (req, res) => {
  const corrStart = Date.now();
  logger.info('GET /api/analytics/correlation - full sequential correlation chain');

  // Step 1: Weather conditions
  logger.info('Correlation Step 1: Weather conditions');
  const weather = await axios.get(`${WEATHER_URL}/api/weather/conditions`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  // Step 2: Active outages (influenced by weather)
  logger.info('Correlation Step 2: Active outages');
  const outages = await axios.get(`${OUTAGE_URL}/api/outages/active`, { timeout: 8000 })
    .then(r => r.data).catch(() => []);

  // Step 3: SCADA alerts (correlated with outages)
  logger.info('Correlation Step 3: SCADA alerts');
  const scadaAlerts = await axios.get(`${SCADA_URL}/api/scada/alerts/active`, { timeout: 8000 })
    .then(r => r.data).catch(() => []);

  // Step 4: Reliability indices (calculated from outage/SCADA data)
  logger.info('Correlation Step 4: Reliability indices');
  const reliability = await axios.get(`${RELIABILITY_URL}/api/reliability/indices`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  // Step 5: Demand forecast (impacted by outages + weather)
  logger.info('Correlation Step 5: Demand forecast');
  const forecast = await axios.get(`${FORECAST_URL}/api/forecast/current`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  const durationMs = Date.now() - corrStart;
  logger.info('Correlation analysis complete', { durationMs, steps: 5 });
  res.json({
    weather,
    activeOutages: outages,
    scadaAlerts,
    reliability,
    forecast,
    correlationDurationMs: durationMs
  });
});

// Operational readiness: grid → crews → dispatches → notifications (mixed pattern)
app.get('/api/operations/readiness', async (req, res) => {
  const readStart = Date.now();
  logger.info('GET /api/operations/readiness - mixed sequential + parallel operations');

  // Step 1: Grid topology baseline (sequential — needed for context)
  logger.info('Readiness Step 1: Grid topology');
  const grid = await axios.get(`${GRID_URL}/api/grid/topology`, { timeout: 8000 })
    .then(r => r.data).catch(() => null);

  // Step 2: Crew + Weather status (parallel)
  logger.info('Readiness Step 2: Crew + Weather status (parallel)');
  const [crewResult, weatherResult] = await Promise.allSettled([
    axios.get(`${CREW_URL}/api/crew/crews`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${WEATHER_URL}/api/weather/conditions`, { timeout: 8000 }).then(r => r.data)
  ]);

  // Step 3: Active dispatches (depends on crew data)
  logger.info('Readiness Step 3: Active dispatches (sequential)');
  const dispatches = await axios.get(`${CREW_URL}/api/crew/dispatches/active`, { timeout: 8000 })
    .then(r => r.data).catch(() => []);

  // Step 4: Notification log + Forecast (parallel)
  logger.info('Readiness Step 4: Notifications + Forecast (parallel)');
  const [notifResult, forecastResult] = await Promise.allSettled([
    axios.get(`${NOTIFICATION_URL}/api/notifications/log`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${FORECAST_URL}/api/forecast/current`, { timeout: 8000 }).then(r => r.data)
  ]);

  const durationMs = Date.now() - readStart;
  logger.info('Readiness assessment complete', { durationMs, steps: 4 });
  res.json({
    grid,
    crews: crewResult.status === 'fulfilled' ? crewResult.value : null,
    weather: weatherResult.status === 'fulfilled' ? weatherResult.value : null,
    activeDispatches: dispatches,
    recentNotifications: notifResult.status === 'fulfilled' ? notifResult.value : null,
    forecast: forecastResult.status === 'fulfilled' ? forecastResult.value : null,
    readinessDurationMs: durationMs
  });
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
