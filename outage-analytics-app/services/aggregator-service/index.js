const express = require('express');
const axios = require('axios');
const winston = require('winston');

const app = express();
app.use(express.json());

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [new winston.transports.Console()]
});

// Service URLs — deep multi-hop calls for rich distributed traces
const OUTAGE_URL = process.env.OUTAGE_SERVICE_URL || 'http://outage-service:3000';
const USAGE_URL = process.env.USAGE_SERVICE_URL || 'http://usage-service:3000';
const SCADA_URL = process.env.SCADA_SERVICE_URL || 'http://scada-service';
const RELIABILITY_URL = process.env.RELIABILITY_SERVICE_URL || 'http://reliability-service:5000';
const FORECAST_URL = process.env.FORECAST_SERVICE_URL || 'http://demand-forecast-service:3000';
const CREW_URL = process.env.CREW_SERVICE_URL || 'http://crew-dispatch-service:3001';
const NOTIFICATION_URL = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:5001';
const WEATHER_URL = process.env.WEATHER_SERVICE_URL || 'http://weather-service:8080';
const GRID_URL = process.env.GRID_SERVICE_URL || 'http://grid-topology-service:3000';
const PRICING_URL = process.env.PRICING_SERVICE_URL || 'http://pricing-service:8000';
const CUSTOMER_URL = process.env.CUSTOMER_SERVICE_URL || 'http://customer-service:4567';

async function safeGet(url, timeout = 8000) {
  try {
    const { data } = await axios.get(url, { timeout });
    return data;
  } catch (err) {
    logger.warn(`Failed to fetch ${url}: ${err.message}`);
    return null;
  }
}

// ============================================================
// Dashboard Aggregation — 5-phase deep call chain
// Creates 5+ hop traces: aggregator → service → service → ...
// ============================================================
app.get('/api/aggregate/dashboard', async (req, res) => {
  const start = Date.now();
  logger.info('Aggregating dashboard — 5-phase deep chain');
  const result = {};

  // Phase 1: Infrastructure baseline (parallel)
  logger.info('Dashboard Phase 1: Infrastructure (grid + SCADA)');
  const [gridStats, scadaSummary] = await Promise.all([
    safeGet(`${GRID_URL}/api/grid/stats`),
    safeGet(`${SCADA_URL}/api/scada/summary`)
  ]);
  result.grid = gridStats;
  result.scada = scadaSummary;

  // Phase 2: Event data (parallel) — depends on infrastructure context
  logger.info('Dashboard Phase 2: Events (outages + weather + alerts)');
  const [outageStats, weatherSummary, scadaAlerts] = await Promise.all([
    safeGet(`${OUTAGE_URL}/api/outages/stats/summary`),
    safeGet(`${WEATHER_URL}/api/weather/summary`),
    safeGet(`${SCADA_URL}/api/scada/alerts?limit=10`)
  ]);
  result.outages = outageStats;
  result.weather = weatherSummary;
  result.scadaAlerts = scadaAlerts;

  // Phase 3: Analytics (sequential — each depends on previous)
  logger.info('Dashboard Phase 3: Analytics (reliability → forecast → pricing)');
  result.reliability = await safeGet(`${RELIABILITY_URL}/api/reliability/indices`);
  result.forecast = await safeGet(`${FORECAST_URL}/api/forecast/summary`);
  result.pricing = await safeGet(`${PRICING_URL}/api/pricing/current`);

  // Phase 4: Operations (parallel)
  logger.info('Dashboard Phase 4: Operations (usage + meter + crew + notifications)');
  const [usage, meter, crew, notif] = await Promise.all([
    safeGet(`${USAGE_URL}/api/usage/summary`),
    safeGet(`${SCADA_URL}/api/scada/summary`),
    safeGet(`${CREW_URL}/api/crew/stats`),
    safeGet(`${NOTIFICATION_URL}/api/notifications/stats`)
  ]);
  result.usage = usage;
  result.meterData = meter;
  result.crewDispatch = crew;
  result.notifications = notif;

  // Phase 5: Customer context enrichment (sequential)
  logger.info('Dashboard Phase 5: Customer enrichment');
  result.customerStats = await safeGet(`${CUSTOMER_URL}/api/customers/stats`);

  const durationMs = Date.now() - start;
  logger.info(`Dashboard aggregation complete`, { durationMs, phases: 5 });
  res.json({ ...result, aggregationDurationMs: durationMs, phases: 5 });
});

// ============================================================
// Outage Deep Enrichment — 6-hop sequential chain
// outage → customer → crew → weather → grid → pricing
// ============================================================
app.get('/api/aggregate/outage/:id', async (req, res) => {
  const start = Date.now();
  const outageId = req.params.id;
  logger.info(`Enriching outage ${outageId} — 6-hop chain`);

  // Hop 1: Base outage data
  logger.info('Hop 1: Outage details');
  const outage = await safeGet(`${OUTAGE_URL}/api/outages/${outageId}`);
  if (!outage) return res.status(404).json({ error: 'Outage not found' });

  // Hop 2: Customer impact data
  logger.info('Hop 2: Customer impact');
  const customerImpact = await safeGet(`${CUSTOMER_URL}/api/customers/region/${encodeURIComponent(outage.location || 'northeast')}`);

  // Hop 3: Crew dispatch details
  logger.info('Hop 3: Crew dispatches');
  const dispatches = await safeGet(`${CREW_URL}/api/crew/dispatches/active`);

  // Hop 4: Weather context for outage region
  logger.info('Hop 4: Weather context');
  const region = outage.region || outage.location || 'northeast';
  const weather = await safeGet(`${WEATHER_URL}/api/weather/region/${encodeURIComponent(region)}`);

  // Hop 5: Grid topology impact
  logger.info('Hop 5: Grid impact');
  const gridImpact = await safeGet(`${GRID_URL}/api/grid/stats`);

  // Hop 6: Pricing impact from outage
  logger.info('Hop 6: Pricing impact');
  const pricingImpact = await safeGet(`${PRICING_URL}/api/pricing/outage-impact?customers=${outage.affectedCustomers || 0}`);

  const durationMs = Date.now() - start;
  logger.info(`Outage enrichment complete`, { outageId, durationMs, hops: 6 });

  res.json({
    outage,
    customerImpact,
    relatedDispatches: dispatches,
    weatherContext: weather,
    gridImpact,
    pricingImpact,
    enrichmentHops: 6,
    enrichmentDurationMs: durationMs
  });
});

// ============================================================
// Full Correlation Analysis — sequential 7-service chain
// weather → outages → SCADA → reliability → forecast → pricing → customer
// ============================================================
app.get('/api/aggregate/correlation', async (req, res) => {
  const start = Date.now();
  logger.info('Full correlation — 7-service sequential chain');

  logger.info('Correlation Step 1: Weather conditions');
  const weather = await safeGet(`${WEATHER_URL}/api/weather/conditions`);

  logger.info('Correlation Step 2: Active outages');
  const outages = await safeGet(`${OUTAGE_URL}/api/outages/active`);

  logger.info('Correlation Step 3: SCADA alerts');
  const scadaAlerts = await safeGet(`${SCADA_URL}/api/scada/alerts/active`);

  logger.info('Correlation Step 4: Reliability indices');
  const reliability = await safeGet(`${RELIABILITY_URL}/api/reliability/indices`);

  logger.info('Correlation Step 5: Demand forecast');
  const forecast = await safeGet(`${FORECAST_URL}/api/forecast/current`);

  logger.info('Correlation Step 6: Current pricing');
  const pricing = await safeGet(`${PRICING_URL}/api/pricing/current`);

  logger.info('Correlation Step 7: Affected customers');
  const customers = await safeGet(`${CUSTOMER_URL}/api/customers/stats`);

  const durationMs = Date.now() - start;
  logger.info('Correlation complete', { durationMs, steps: 7 });

  res.json({
    weather, activeOutages: outages, scadaAlerts, reliability,
    forecast, pricing, customerStats: customers,
    correlationSteps: 7, correlationDurationMs: durationMs
  });
});

// ============================================================
// Operational Readiness — mixed sequential + parallel
// ============================================================
app.get('/api/aggregate/operations', async (req, res) => {
  const start = Date.now();
  logger.info('Operational readiness — mixed chain');

  // Step 1: Grid baseline (sequential)
  const grid = await safeGet(`${GRID_URL}/api/grid/topology`);

  // Step 2: Crew + Weather + Customer (parallel)
  const [crews, weather, customerStats] = await Promise.all([
    safeGet(`${CREW_URL}/api/crew/crews`),
    safeGet(`${WEATHER_URL}/api/weather/conditions`),
    safeGet(`${CUSTOMER_URL}/api/customers/stats`)
  ]);

  // Step 3: Active dispatches (depends on crew)
  const dispatches = await safeGet(`${CREW_URL}/api/crew/dispatches/active`);

  // Step 4: Notifications + Forecast + Pricing (parallel)
  const [notifications, forecast, pricing] = await Promise.all([
    safeGet(`${NOTIFICATION_URL}/api/notifications/log`),
    safeGet(`${FORECAST_URL}/api/forecast/current`),
    safeGet(`${PRICING_URL}/api/pricing/current`)
  ]);

  const durationMs = Date.now() - start;
  res.json({
    grid, crews, weather, customerStats, activeDispatches: dispatches,
    recentNotifications: notifications, forecast, pricing,
    readinessDurationMs: durationMs
  });
});

// ============================================================
// Report Generation — compiles data for CSV/PDF export
// ============================================================
app.get('/api/aggregate/report/:type', async (req, res) => {
  const start = Date.now();
  const reportType = req.params.type;
  logger.info(`Generating ${reportType} report`);

  let reportData = {};
  switch (reportType) {
    case 'outages':
      const [outages, outageStats, relIndices] = await Promise.all([
        safeGet(`${OUTAGE_URL}/api/outages`),
        safeGet(`${OUTAGE_URL}/api/outages/stats/summary`),
        safeGet(`${RELIABILITY_URL}/api/reliability/indices`)
      ]);
      reportData = { outages, stats: outageStats, reliability: relIndices };
      break;
    case 'reliability':
      const [indices, history] = await Promise.all([
        safeGet(`${RELIABILITY_URL}/api/reliability/indices`),
        safeGet(`${RELIABILITY_URL}/api/reliability/history?days=30`)
      ]);
      reportData = { currentIndices: indices, history };
      break;
    case 'crew':
      const [crewStats, allCrews, allDispatches] = await Promise.all([
        safeGet(`${CREW_URL}/api/crew/stats`),
        safeGet(`${CREW_URL}/api/crew/crews`),
        safeGet(`${CREW_URL}/api/crew/dispatches?limit=100`)
      ]);
      reportData = { stats: crewStats, crews: allCrews, dispatches: allDispatches };
      break;
    case 'metering':
      const [meterSummary, readings, anomalies] = await Promise.all([
        safeGet(`${USAGE_URL}/api/usage/summary`),
        safeGet(`${SCADA_URL}/api/scada/readings/latest`),
        safeGet(`${SCADA_URL}/api/scada/alerts?limit=50`)
      ]);
      reportData = { summary: meterSummary, readings, anomalies };
      break;
    default:
      return res.status(400).json({ error: `Unknown report type: ${reportType}. Available: outages, reliability, crew, metering` });
  }

  const durationMs = Date.now() - start;
  reportData.reportType = reportType;
  reportData.generatedAt = new Date().toISOString();
  reportData.generationDurationMs = durationMs;
  res.json(reportData);
});

// Health check
app.get('/api/aggregate/health', (req, res) => {
  res.json({ status: 'Healthy', service: 'aggregator-service', timestamp: new Date().toISOString() });
});

const port = process.env.PORT || 3002;
app.listen(port, () => {
  logger.info(`Aggregator service running on port ${port}`);
});
