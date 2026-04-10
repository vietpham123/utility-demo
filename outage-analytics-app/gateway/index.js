const express = require('express');
const axios = require('axios');
const logger = require('./logger');
const app = express();
app.use(express.json());

// ============================================================
// Dynatrace Business Events Integration
// Sends CloudEvents to the Dynatrace Biz Events Ingest API
// ============================================================
const DT_TENANT_URL = process.env.DT_TENANT_URL || '';       // e.g. https://<tenant>.apps.dynatrace.com
const DT_BIZEVENT_TOKEN = process.env.DT_BIZEVENT_TOKEN || ''; // API token with bizevents.ingest scope
const DT_BIZEVENT_ENABLED = !!(DT_TENANT_URL && DT_BIZEVENT_TOKEN);
const EVENT_PROVIDER = 'genericutility.event.provider';

if (DT_BIZEVENT_ENABLED) {
  logger.info('Dynatrace Business Events ENABLED', { tenant: DT_TENANT_URL });
} else {
  logger.info('Dynatrace Business Events DISABLED (set DT_TENANT_URL and DT_BIZEVENT_TOKEN to enable)');
}

/**
 * Send a business event to Dynatrace Biz Events Ingest API.
 * @param {string} eventType - CloudEvent type (e.g. 'outage.created')
 * @param {object} data - Event payload
 */
async function sendBizEvent(eventType, data) {
  if (!DT_BIZEVENT_ENABLED) return;
  const cloudEvent = {
    specversion: '1.0',
    id: `${eventType}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    source: EVENT_PROVIDER,
    type: eventType,
    time: new Date().toISOString(),
    data
  };
  try {
    await axios.post(
      `${DT_TENANT_URL}/api/v2/bizevents/ingest`,
      cloudEvent,
      {
        headers: {
          'Content-Type': 'application/cloudevent+json',
          Authorization: `Api-Token ${DT_BIZEVENT_TOKEN}`
        },
        timeout: 5000
      }
    );
    logger.debug('BizEvent sent', { type: eventType });
  } catch (err) {
    logger.warn('BizEvent send failed', { type: eventType, error: err.message });
  }
}

/**
 * Send multiple business events in a batch (fire-and-forget).
 * @param {Array<{type: string, data: object}>} events
 */
function sendBizEvents(events) {
  if (!DT_BIZEVENT_ENABLED) return;
  events.forEach(e => sendBizEvent(e.type, e.data));
}

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

// Phase 1-3 new service URLs
const AGGREGATOR_URL = process.env.AGGREGATOR_SERVICE_URL || 'http://aggregator-service:3002';
const CUSTOMER_URL = process.env.CUSTOMER_SERVICE_URL || 'http://customer-service:4567';
const AUDIT_URL = process.env.AUDIT_SERVICE_URL || 'http://audit-service:8090';
const PRICING_URL = process.env.PRICING_SERVICE_URL || 'http://pricing-service:8000';
const WORK_ORDER_URL = process.env.WORK_ORDER_SERVICE_URL || 'http://work-order-service:4000';
const ALERT_CORR_URL = process.env.ALERT_CORRELATION_SERVICE_URL || 'http://alert-correlation-service:8070';

// ============================================================
// Fault Injection Engine — togglable failure scenarios for Dynatrace demos
// Injects real HTTP 500 errors with exception traces that Davis AI detects
// ============================================================
const faultState = {
  enabled: false,
  scenario: null,         // 'database-outage', 'cascade-failure', 'resource-exhaustion', 'network-partition'
  startedAt: null,
  errorCount: 0,
  requestCount: 0,
  affectedServices: [],   // which service routes are affected
  failureRate: 0.75       // % of requests that fail (default 75%)
};

const FAULT_SCENARIOS = {
  'database-outage': {
    description: 'TimescaleDB connection pool exhausted — outage + usage + reliability services fail',
    affectedServices: ['outage', 'usage', 'reliability', 'meter-data'],
    failureRate: 0.80,
    errors: [
      { status: 500, message: 'FATAL: remaining connection slots are reserved for superuser connections', code: 'ECONNREFUSED' },
      { status: 500, message: 'Error: connect ECONNREFUSED 10.0.0.5:5432 - PostgreSQL connection pool exhausted', code: 'POOL_EXHAUSTED' },
      { status: 500, message: 'TimeoutError: ResourceRequest timed out - pg pool max connections (10) reached', code: 'TIMEOUT' },
      { status: 503, message: 'ServiceUnavailableError: Database health check failed after 3 retries', code: 'DB_HEALTH_FAILED' }
    ]
  },
  'cascade-failure': {
    description: 'SCADA service timeout causes cascading failures across outage detection + grid + reliability',
    affectedServices: ['scada', 'outage', 'grid', 'reliability', 'crew'],
    failureRate: 0.70,
    errors: [
      { status: 500, message: 'Error: socket hang up - SCADA telemetry stream interrupted', code: 'ECONNRESET' },
      { status: 504, message: 'GatewayTimeoutError: upstream SCADA service did not respond within 8000ms', code: 'GATEWAY_TIMEOUT' },
      { status: 500, message: 'Error: SCADA data pipeline stalled — no readings received in 30s, triggering failover', code: 'PIPELINE_STALL' },
      { status: 502, message: 'BadGatewayError: SCADA service returned malformed response (truncated JSON)', code: 'BAD_GATEWAY' }
    ]
  },
  'resource-exhaustion': {
    description: 'Memory pressure + thread pool exhaustion across Java/Python services',
    affectedServices: ['meter-data', 'reliability', 'forecast', 'weather'],
    failureRate: 0.65,
    errors: [
      { status: 500, message: 'java.lang.OutOfMemoryError: GC overhead limit exceeded - HikariPool connection leak detected', code: 'OOM' },
      { status: 500, message: 'MemoryError: Unable to allocate 256 MiB for reliability matrix computation', code: 'MEMORY_ERROR' },
      { status: 500, message: 'Error: worker_threads pool exhausted - all 4 workers busy processing forecast models', code: 'THREAD_POOL' },
      { status: 503, message: 'ServiceUnavailableError: Container memory limit (512Mi) approaching — 498Mi used', code: 'RESOURCE_LIMIT' }
    ]
  },
  'network-partition': {
    description: 'Kafka + RabbitMQ broker connectivity lost — async messaging fails, crew dispatch + notifications impacted',
    affectedServices: ['crew', 'notifications', 'scada', 'outage'],
    failureRate: 0.85,
    errors: [
      { status: 500, message: 'KafkaJSConnectionError: Connection timeout to kafka:9092 — broker unreachable', code: 'KAFKA_CONN' },
      { status: 500, message: 'Error: Channel closed by server: 320 (CONNECTION-FORCED) — RabbitMQ node unreachable', code: 'AMQP_CLOSED' },
      { status: 500, message: 'Error: connect ETIMEDOUT 10.0.0.12:9092 — network partition detected between AZ-1 and AZ-2', code: 'ETIMEDOUT' },
      { status: 502, message: 'BadGatewayError: Message broker health check failed — 0 of 3 brokers responding', code: 'BROKER_DOWN' }
    ]
  }
};

// Fault injection API endpoints
app.post('/api/fault/inject', (req, res) => {
  const scenario = req.body.scenario || 'database-outage';
  const config = FAULT_SCENARIOS[scenario];
  if (!config) {
    return res.status(400).json({ error: `Unknown scenario. Available: ${Object.keys(FAULT_SCENARIOS).join(', ')}` });
  }
  faultState.enabled = true;
  faultState.scenario = scenario;
  faultState.startedAt = new Date().toISOString();
  faultState.errorCount = 0;
  faultState.requestCount = 0;
  faultState.affectedServices = config.affectedServices;
  faultState.failureRate = req.body.failureRate || config.failureRate;
  logger.error(`🔴 FAULT INJECTION ENABLED: ${scenario}`, {
    description: config.description,
    affectedServices: config.affectedServices,
    failureRate: faultState.failureRate
  });

  // Propagate fault mode to individual services (best-effort)
  if (config.affectedServices.includes('outage')) {
    axios.post(`${OUTAGE_URL}/api/outages/fault/enable`, {}, { timeout: 3000 }).catch(() => {});
  }
  if (config.affectedServices.includes('usage')) {
    axios.post(`${USAGE_URL}/api/usage/fault/enable`, {}, { timeout: 3000 }).catch(() => {});
  }

  res.json({
    status: 'Fault injection ENABLED',
    scenario,
    description: config.description,
    affectedServices: config.affectedServices,
    failureRate: faultState.failureRate,
    startedAt: faultState.startedAt,
    note: 'Dynatrace should detect failure rate increase within 2-5 minutes'
  });
});

app.post('/api/fault/clear', (req, res) => {
  const summary = {
    scenario: faultState.scenario,
    duration: faultState.startedAt ? `${Math.round((Date.now() - new Date(faultState.startedAt).getTime()) / 1000)}s` : null,
    totalErrors: faultState.errorCount,
    totalRequests: faultState.requestCount
  };
  faultState.enabled = false;
  faultState.scenario = null;
  faultState.startedAt = null;
  faultState.affectedServices = [];
  logger.info('🟢 FAULT INJECTION CLEARED', summary);

  // Propagate fault clear to individual services (best-effort)
  axios.post(`${OUTAGE_URL}/api/outages/fault/disable`, {}, { timeout: 3000 }).catch(() => {});
  axios.post(`${USAGE_URL}/api/usage/fault/disable`, {}, { timeout: 3000 }).catch(() => {});

  res.json({ status: 'Fault injection CLEARED', summary });
});

app.get('/api/fault/status', (req, res) => {
  res.json({
    enabled: faultState.enabled,
    scenario: faultState.scenario,
    startedAt: faultState.startedAt,
    affectedServices: faultState.affectedServices,
    failureRate: faultState.failureRate,
    errorCount: faultState.errorCount,
    requestCount: faultState.requestCount,
    availableScenarios: Object.entries(FAULT_SCENARIOS).map(([k, v]) => ({
      name: k, description: v.description, services: v.affectedServices, defaultRate: v.failureRate
    }))
  });
});

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

  // ---- FAULT INJECTION MIDDLEWARE ----
  if (faultState.enabled && req.path !== '/api/health' && !req.path.startsWith('/api/fault/')) {
    faultState.requestCount++;
    // Check if this request's service route is affected
    const matchedService = faultState.affectedServices.find(svc =>
      req.path.includes(`/api/${svc}`) ||
      (svc === 'outage' && req.path.includes('/api/outages')) ||
      (svc === 'notifications' && req.path.includes('/api/notifications')) ||
      (svc === 'crew' && req.path.includes('/api/crew'))
    );
    if (matchedService && Math.random() < faultState.failureRate) {
      faultState.errorCount++;
      const scenario = FAULT_SCENARIOS[faultState.scenario];
      const errorTemplate = scenario.errors[Math.floor(Math.random() * scenario.errors.length)];
      // Throw a real error so Dynatrace captures the exception
      const err = new Error(errorTemplate.message);
      err.code = errorTemplate.code;
      err.service = matchedService;
      err.scenario = faultState.scenario;
      logger.error(`FAULT INJECTED: ${errorTemplate.code}`, {
        path: req.path,
        service: matchedService,
        scenario: faultState.scenario,
        errorMessage: errorTemplate.message
      });
      return res.status(errorTemplate.status).json({
        error: errorTemplate.message,
        code: errorTemplate.code,
        service: matchedService,
        timestamp: new Date().toISOString()
      });
    }
  }

  // ~2% chance: sporadic gateway timeout simulation
  if (Math.random() < 0.02 && req.path !== '/api/health' && req.path !== '/api/simulate/cycle' && !req.path.startsWith('/api/fault/')) {
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

// Aggregator Service routes (Node.js — deep multi-hop orchestration)
app.get('/api/aggregate/dashboard', proxy(AGGREGATOR_URL));
app.get('/api/aggregate/outage/:id', proxy(AGGREGATOR_URL));
app.get('/api/aggregate/correlation', proxy(AGGREGATOR_URL));
app.get('/api/aggregate/operations', proxy(AGGREGATOR_URL));
app.get('/api/aggregate/report/:type', proxy(AGGREGATOR_URL));

// Customer Service routes (Ruby/Sinatra)
app.post('/api/auth/login', proxy(CUSTOMER_URL));
app.post('/api/auth/register', proxy(CUSTOMER_URL));
app.post('/api/auth/logout', proxy(CUSTOMER_URL));
app.get('/api/auth/me', proxy(CUSTOMER_URL));
app.get('/api/auth/users', proxy(CUSTOMER_URL));
app.put('/api/auth/preferences', proxy(CUSTOMER_URL));
app.get('/api/customers', proxy(CUSTOMER_URL));
app.get('/api/customers/search', proxy(CUSTOMER_URL));
app.get('/api/customers/stats', proxy(CUSTOMER_URL));
app.get('/api/customers/region/:region', proxy(CUSTOMER_URL));
app.get('/api/customers/:id', proxy(CUSTOMER_URL));

// Audit Service routes (Kotlin/Ktor)
app.get('/api/audit/log', proxy(AUDIT_URL));
app.get('/api/audit/stats', proxy(AUDIT_URL));
app.get('/api/audit/search', proxy(AUDIT_URL));
app.post('/api/audit/log', proxy(AUDIT_URL));

// Pricing Service routes (PHP)
app.get('/api/pricing/current', proxy(PRICING_URL));
app.get('/api/pricing/calculate', proxy(PRICING_URL));
app.get('/api/pricing/rates', proxy(PRICING_URL));
app.get('/api/pricing/regions', proxy(PRICING_URL));
app.get('/api/pricing/outage-impact', proxy(PRICING_URL));

// Work Order Service routes (Elixir/Plug)
app.get('/api/work-orders', proxy(WORK_ORDER_URL));
app.get('/api/work-orders/stats', proxy(WORK_ORDER_URL));
app.get('/api/work-orders/:id', proxy(WORK_ORDER_URL));
app.post('/api/work-orders', proxy(WORK_ORDER_URL));
app.put('/api/work-orders/:id', proxy(WORK_ORDER_URL));

// Alert Correlation Service routes (Rust/Actix)
app.get('/api/alerts/correlated', proxy(ALERT_CORR_URL));
app.get('/api/alerts/stats', proxy(ALERT_CORR_URL));
app.post('/api/alerts/correlate', proxy(ALERT_CORR_URL));

// Global Search — queries multiple services in parallel
app.get('/api/search', async (req, res) => {
  const q = req.query.q || '';
  if (!q) return res.json({ results: [] });
  logger.info('GET /api/search', { query: q });
  const [outages, customers, meters, crews, workOrders, auditLogs] = await Promise.allSettled([
    axios.get(`${OUTAGE_URL}/api/outages`, { timeout: 5000 }).then(r => {
      const items = Array.isArray(r.data) ? r.data : r.data.outages || [];
      return items.filter(o => JSON.stringify(o).toLowerCase().includes(q.toLowerCase())).slice(0, 10);
    }),
    axios.get(`${CUSTOMER_URL}/api/customers/search?q=${encodeURIComponent(q)}`, { timeout: 5000 }).then(r => r.data.customers || []),
    axios.get(`${METER_URL}/api/meter-data/meters`, { timeout: 5000 }).then(r => {
      const items = Array.isArray(r.data) ? r.data : r.data.meters || [];
      return items.filter(m => JSON.stringify(m).toLowerCase().includes(q.toLowerCase())).slice(0, 10);
    }),
    axios.get(`${CREW_URL}/api/crew/crews`, { timeout: 5000 }).then(r => {
      const items = Array.isArray(r.data) ? r.data : r.data.crews || [];
      return items.filter(c => JSON.stringify(c).toLowerCase().includes(q.toLowerCase())).slice(0, 10);
    }),
    axios.get(`${WORK_ORDER_URL}/api/work-orders`, { timeout: 5000 }).then(r => {
      const items = Array.isArray(r.data) ? r.data : r.data.workOrders || [];
      return items.filter(w => JSON.stringify(w).toLowerCase().includes(q.toLowerCase())).slice(0, 10);
    }),
    axios.get(`${AUDIT_URL}/api/audit/search?q=${encodeURIComponent(q)}`, { timeout: 5000 }).then(r => r.data.entries || [])
  ]);
  res.json({
    query: q,
    results: {
      outages: outages.status === 'fulfilled' ? outages.value : [],
      customers: customers.status === 'fulfilled' ? customers.value : [],
      meters: meters.status === 'fulfilled' ? meters.value : [],
      crews: crews.status === 'fulfilled' ? crews.value : [],
      workOrders: workOrders.status === 'fulfilled' ? workOrders.value : [],
      auditLogs: auditLogs.status === 'fulfilled' ? auditLogs.value : []
    }
  });
});

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

  // Wave 6: Extended services (parallel) — pricing queries, alert correlation, work order creation
  logger.info('Simulation Wave 6: Extended services (pricing + alerts + work-orders + audit)');
  await Promise.allSettled([
    axios.get(`${PRICING_URL}/api/pricing/current`, { timeout: 10000 })
      .then(r => { results.pricing = r.data; })
      .catch(err => { results.pricing = { error: err.message }; }),
    axios.post(`${ALERT_CORR_URL}/api/alerts/correlate`, {}, { timeout: 10000 })
      .then(r => { results.alertCorrelation = r.data; })
      .catch(err => { results.alertCorrelation = { error: err.message }; }),
    axios.get(`${WORK_ORDER_URL}/api/work-orders/stats`, { timeout: 10000 })
      .then(r => { results.workOrders = r.data; })
      .catch(err => { results.workOrders = { error: err.message }; }),
    axios.get(`${AUDIT_URL}/api/audit/stats`, { timeout: 10000 })
      .then(r => { results.audit = r.data; })
      .catch(err => { results.audit = { error: err.message }; })
  ]);

  const durationMs = Date.now() - cycleStart;
  logger.info('Simulation cycle complete', { durationMs, waves: 6, services: Object.keys(results).length });

  // ---- Dynatrace Business Events: emit events from simulation results ----
  const bizEvents = [];
  const region = ['northeast', 'southeast', 'midwest', 'southwest', 'northwest', 'central'][Math.floor(Math.random() * 6)];

  // SCADA telemetry event
  if (results.scada && !results.scada.error) {
    const s = results.scada;
    bizEvents.push({ type: 'scada.telemetry.received', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      sensors: s.sensorsGenerated || s.sensors || 1,
      alerts: s.alertsGenerated || s.alerts || 0,
      status: s.status || 'ok',
      timestamp: new Date().toISOString()
    }});
  }

  // Weather observation event
  if (results.weather && !results.weather.error) {
    const w = results.weather;
    bizEvents.push({ type: 'weather.observation.recorded', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'temperature.f': w.temperatureF || w.temperature || null,
      'wind.speed.mph': w.windSpeedMph || w.windSpeed || null,
      severity: w.severity || 'none',
      condition: w.condition || 'clear',
      'storm.mode': w.stormModeActive || false,
      timestamp: new Date().toISOString()
    }});
  }

  // Weather correlation event
  if (results.weatherCorrelation && !results.weatherCorrelation.error) {
    const wc = results.weatherCorrelation;
    bizEvents.push({ type: 'weather.correlation.completed', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'correlation.score': wc.correlationScore || wc.score || null,
      'weather.related': wc.weatherRelated || false,
      'risk.level': wc.riskLevel || 'low',
      timestamp: new Date().toISOString()
    }});
  }

  // Outage event
  if (results.outage && !results.outage.error) {
    const o = results.outage;
    const outageData = o.outage || o;
    bizEvents.push({ type: 'outage.detected', data: {
      'event.provider': EVENT_PROVIDER,
      'outage.id': outageData.id || o.outageId || `OUT-${Date.now()}`,
      region,
      cause: outageData.cause || o.cause || 'unknown',
      'customers.affected': outageData.affectedCustomers || outageData.customersAffected || o.customersAffected || 0,
      priority: outageData.priority || o.priority || 'medium',
      'equipment.type': outageData.equipmentType || o.equipmentType || 'unknown',
      status: outageData.status || 'Active',
      timestamp: new Date().toISOString()
    }});
  }

  // Usage event
  if (results.usage && !results.usage.error) {
    const u = results.usage;
    bizEvents.push({ type: 'usage.reading.recorded', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'customer.id': u.customerId || 'CUST-sim',
      'usage.kwh': u.usageKWh || u.totalKWh || 0,
      'peak.kw': u.peakKW || 0,
      'total.readings': u.totalReadings || u.readingsCount || 1,
      timestamp: new Date().toISOString()
    }});
  }

  // Meter data event
  if (results.meter && !results.meter.error) {
    const m = results.meter;
    bizEvents.push({ type: 'meter.reading.validated', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'meter.id': m.meterId || 'MTR-sim',
      'reading.kwh': m.readingKwh || m.totalKwh || 0,
      'voltage.v': m.voltageV || 0,
      'power.factor': m.powerFactor || 0,
      'quality.flag': m.qualityFlag || 'normal',
      anomalies: m.anomaliesDetected || m.anomalies || 0,
      timestamp: new Date().toISOString()
    }});
    // Emit anomaly bizevent if detected
    if ((m.anomaliesDetected || m.anomalies || 0) > 0) {
      bizEvents.push({ type: 'meter.anomaly.detected', data: {
        'event.provider': EVENT_PROVIDER,
        region,
        'meter.id': m.meterId || 'MTR-sim',
        'anomaly.type': m.anomalyType || 'usage_spike',
        severity: m.severity || 'medium',
        timestamp: new Date().toISOString()
      }});
    }
  }

  // Forecast event
  if (results.forecast && !results.forecast.error) {
    const f = results.forecast;
    bizEvents.push({ type: 'demand.forecast.generated', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'peak.demand.mw': f.peakDemandMW || f.peakDemand || 0,
      'forecast.confidence': f.confidence || 0,
      'load.factor': f.loadFactor || 0,
      timestamp: new Date().toISOString()
    }});
  }

  // Reliability event
  if (results.reliability && !results.reliability.error) {
    const r = results.reliability;
    bizEvents.push({ type: 'reliability.calculated', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      saidi: r.saidi || r.SAIDI || 0,
      saifi: r.saifi || r.SAIFI || 0,
      caidi: r.caidi || r.CAIDI || 0,
      maifi: r.maifi || r.MAIFI || 0,
      'total.interruptions': r.totalInterruptions || 0,
      'total.customer.minutes': r.totalCustomerMinutes || 0,
      timestamp: new Date().toISOString()
    }});
  }

  // Crew dispatch event
  if (results.crew && !results.crew.error) {
    const c = results.crew;
    const dispatch = c.dispatch || c;
    bizEvents.push({ type: 'crew.dispatched', data: {
      'event.provider': EVENT_PROVIDER,
      'dispatch.id': dispatch.dispatchId || dispatch.id || `DSP-${Date.now()}`,
      region,
      'crew.name': dispatch.crewName || dispatch.crew || 'unknown',
      priority: dispatch.priority || 'medium',
      'affected.customers': dispatch.affectedCustomers || 0,
      'etr.minutes': dispatch.etrMinutes || dispatch.etr || 0,
      status: dispatch.status || 'Dispatched',
      timestamp: new Date().toISOString()
    }});
  }

  // Notification event
  if (results.notifications && !results.notifications.error) {
    const n = results.notifications;
    bizEvents.push({ type: 'notification.sent', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      channel: n.channel || 'multi',
      'total.sent': n.totalSent || n.sent || 1,
      'delivery.success': n.deliverySuccess || n.delivered || 0,
      'delivery.failed': n.deliveryFailed || n.failed || 0,
      timestamp: new Date().toISOString()
    }});
  }

  // Alert correlation event
  if (results.alertCorrelation && !results.alertCorrelation.error) {
    const ac = results.alertCorrelation;
    bizEvents.push({ type: 'alert.correlated', data: {
      'event.provider': EVENT_PROVIDER,
      region,
      'correlated.alerts': ac.correlatedAlerts || ac.total || 0,
      'risk.score': ac.riskScore || 0,
      timestamp: new Date().toISOString()
    }});
  }

  // Fire all business events (non-blocking)
  sendBizEvents(bizEvents);

  res.json({ status: 'Cycle complete', durationMs, bizEventsSent: bizEvents.length, results });
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

  // Phase 5: New services data (parallel) — pricing, customers, work orders, alerts, audit
  logger.info('Dashboard Phase 5: Extended services (pricing + customers + work-orders + alerts + audit)');
  const [pricingResult, customerResult, workOrderResult, alertResult, auditResult] = await Promise.allSettled([
    axios.get(`${PRICING_URL}/api/pricing/current`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${CUSTOMER_URL}/api/customers/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${WORK_ORDER_URL}/api/work-orders/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${ALERT_CORR_URL}/api/alerts/stats`, { timeout: 8000 }).then(r => r.data),
    axios.get(`${AUDIT_URL}/api/audit/stats`, { timeout: 8000 }).then(r => r.data)
  ]);
  results.pricing = pricingResult.status === 'fulfilled' ? pricingResult.value : null;
  results.customers = customerResult.status === 'fulfilled' ? customerResult.value : null;
  results.workOrders = workOrderResult.status === 'fulfilled' ? workOrderResult.value : null;
  results.alertCorrelation = alertResult.status === 'fulfilled' ? alertResult.value : null;
  results.auditLog = auditResult.status === 'fulfilled' ? auditResult.value : null;

  const durationMs = Date.now() - dashStart;
  logger.info('Dashboard aggregation complete', { durationMs, phases: 5 });
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
    { name: 'weather-service', url: `${WEATHER_URL}/api/weather/health` },
    { name: 'aggregator-service', url: `${AGGREGATOR_URL}/api/aggregate/health` },
    { name: 'customer-service', url: `${CUSTOMER_URL}/api/customers/stats` },
    { name: 'audit-service', url: `${AUDIT_URL}/api/audit/health` },
    { name: 'pricing-service', url: `${PRICING_URL}/api/pricing/health` },
    { name: 'work-order-service', url: `${WORK_ORDER_URL}/api/work-orders/health` },
    { name: 'alert-correlation-service', url: `${ALERT_CORR_URL}/api/alerts/health` }
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

const http = require('http');
const WebSocket = require('ws');

const port = process.env.PORT || 3000;
const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/ws' });

// WebSocket: broadcast live events to all connected UI clients
const wsClients = new Set();
wss.on('connection', (ws) => {
  wsClients.add(ws);
  logger.info('WebSocket client connected', { total: wsClients.size });
  ws.send(JSON.stringify({ type: 'connected', timestamp: new Date().toISOString() }));
  ws.on('close', () => { wsClients.delete(ws); });
});

function broadcastEvent(event) {
  const msg = JSON.stringify(event);
  wsClients.forEach(ws => { if (ws.readyState === WebSocket.OPEN) ws.send(msg); });
}

// Periodic live event broadcaster — sends simulated events every 10s
setInterval(() => {
  if (wsClients.size === 0) return;
  const eventTypes = ['outage_detected', 'scada_alert', 'crew_dispatched', 'weather_warning', 'work_order_created', 'meter_anomaly', 'pricing_update'];
  const regions = ['northeast', 'southeast', 'midwest', 'southwest', 'northwest', 'central'];
  const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];
  broadcastEvent({
    type,
    region: regions[Math.floor(Math.random() * regions.length)],
    severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)],
    message: `Live event: ${type.replace(/_/g, ' ')}`,
    timestamp: new Date().toISOString()
  });
}, 10000);

server.listen(port, () => {
  logger.info(`Analytics Gateway v2.0 running on port ${port} (HTTP + WebSocket)`);

  // Periodic simulation trigger
  const SIMULATE_INTERVAL = parseInt(process.env.SIMULATE_INTERVAL || '15000');
  setTimeout(() => {
    logger.info(`Starting simulation orchestrator (interval: ${SIMULATE_INTERVAL}ms)`);
    setInterval(() => {
      axios.post(`http://localhost:${port}/api/simulate/cycle`, {}, { timeout: 30000 })
        .then(r => logger.info('Simulation cycle triggered', { durationMs: r.data.durationMs }))
        .catch(err => logger.warn('Simulation cycle failed', { error: err.message }));
    }, SIMULATE_INTERVAL);
  }, 30000);
});
