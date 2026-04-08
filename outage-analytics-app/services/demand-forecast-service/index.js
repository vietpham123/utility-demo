const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const { Kafka } = require('kafkajs');
const logger = require('./logger');

const app = express();
app.use(express.json());

const pool = new Pool({
  host: process.env.DB_HOST || 'timescaledb',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'utilitydb',
  user: process.env.DB_USER || 'utilityuser',
  password: process.env.DB_PASSWORD || 'utility2026!',
  max: 5
});

const redis = new Redis({
  host: process.env.REDIS_HOST || 'redis',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times) => Math.min(times * 100, 3000)
});
redis.on('error', () => {});

const kafka = new Kafka({
  clientId: 'demand-forecast-service',
  brokers: [(process.env.KAFKA_BROKER || 'kafka:9092')]
});
let producer = null;

// ============================================================
// Sporadic error injection & request logging
// ============================================================
let forecastCycleCount = 0;

app.use((req, res, next) => {
  const start = Date.now();
  logger.debug('Incoming request', { method: req.method, path: req.path });

  res.on('finish', () => {
    const duration = Date.now() - start;
    const meta = { method: req.method, path: req.path, status: res.statusCode, durationMs: duration };
    if (res.statusCode >= 500) {
      logger.error('Forecast request failed', meta);
    } else if (duration > 3000) {
      logger.warn('Slow forecast computation', meta);
    } else {
      logger.debug('Request completed', meta);
    }
  });
  next();
});

// Areas: 3 substations + system-wide
const areas = [
  { id: 'SUB-001', name: 'Lakeside Substation', type: 'substation', baseLoadMw: 280, peakCapacityMw: 450 },
  { id: 'SUB-002', name: 'Harbor Point Substation', type: 'substation', baseLoadMw: 220, peakCapacityMw: 380 },
  { id: 'SUB-003', name: 'Liberty Grid Substation', type: 'substation', baseLoadMw: 350, peakCapacityMw: 520 },
  { id: 'SYSTEM', name: 'System Total', type: 'system', baseLoadMw: 850, peakCapacityMw: 1350 }
];

let currentForecasts = [];
let forecastHistory = [];

// Weather simulation
function getSimulatedWeather(hour) {
  const month = new Date().getMonth();
  const isSummer = month >= 5 && month <= 8;
  const isWinter = month <= 1 || month >= 11;
  const baseTemp = isSummer ? 82 : isWinter ? 32 : 58;
  const diurnalSwing = isSummer ? 15 : 10;
  const hourFactor = Math.sin((hour - 6) * Math.PI / 12);
  const temp = baseTemp + diurnalSwing * hourFactor + (Math.random() - 0.5) * 8;
  const humidity = isSummer ? 60 + Math.random() * 25 : 40 + Math.random() * 30;
  return { temperatureF: Math.round(temp * 10) / 10, humidityPct: Math.round(humidity * 10) / 10 };
}

// Load forecasting model (simplified)
function forecastLoad(area, hour, weather) {
  const { temperatureF } = weather;
  // Temperature-load relationship: U-shaped curve centered at 65°F
  const tempDeviation = Math.abs(temperatureF - 65);
  const tempFactor = 1.0 + (tempDeviation / 40) * 0.35;

  // Time-of-day pattern
  const isWeekday = new Date().getDay() >= 1 && new Date().getDay() <= 5;
  let timeFactor;
  if (hour >= 7 && hour <= 9) timeFactor = isWeekday ? 0.85 : 0.6; // morning ramp
  else if (hour >= 10 && hour <= 14) timeFactor = 0.9; // midday
  else if (hour >= 15 && hour <= 19) timeFactor = 1.0; // peak
  else if (hour >= 20 && hour <= 22) timeFactor = 0.75; // evening
  else timeFactor = 0.45; // overnight

  const baseMw = area.baseLoadMw * tempFactor * timeFactor;
  const noise = 0.95 + Math.random() * 0.1;
  const forecastMw = Math.round(baseMw * noise * 100) / 100;

  // Confidence interval widens for hours further ahead
  const hoursAhead = (hour - new Date().getHours() + 24) % 24;
  const uncertainty = 0.02 + hoursAhead * 0.005;
  const confidenceLow = Math.round(forecastMw * (1 - uncertainty) * 100) / 100;
  const confidenceHigh = Math.round(forecastMw * (1 + uncertainty) * 100) / 100;

  return { forecastMw, confidenceLow, confidenceHigh };
}

// Generate 24-hour forecast
function generateForecasts() {
  const now = new Date();
  const forecasts = [];

  for (const area of areas) {
    for (let h = 0; h < 24; h++) {
      const forecastTime = new Date(now);
      forecastTime.setHours(h, 0, 0, 0);
      const weather = getSimulatedWeather(h);
      const { forecastMw, confidenceLow, confidenceHigh } = forecastLoad(area, h, weather);

      // For past hours today, generate an "actual" value close to forecast
      const isPast = h < now.getHours();
      const actualMw = isPast ? Math.round((forecastMw * (0.95 + Math.random() * 0.1)) * 100) / 100 : null;

      forecasts.push({
        time: forecastTime.toISOString(),
        areaId: area.id,
        areaType: area.type,
        areaName: area.name,
        forecastMw,
        actualMw,
        temperatureF: weather.temperatureF,
        humidityPct: weather.humidityPct,
        confidenceLow,
        confidenceHigh,
        hour: h,
        peakCapacityMw: area.peakCapacityMw,
        utilizationPct: Math.round((forecastMw / area.peakCapacityMw) * 10000) / 100
      });
    }
  }

  currentForecasts = forecasts;
  return forecasts;
}

// Persist and publish forecasts
async function persistForecasts(forecasts) {
  // Store in TimescaleDB
  try {
    const client = await pool.connect();
    for (const f of forecasts) {
      await client.query(
        `INSERT INTO timeseries.demand_forecasts (time, area_id, area_type, forecast_mw, actual_mw, temperature_f, humidity_pct, confidence_low, confidence_high)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
         ON CONFLICT DO NOTHING`,
        [f.time, f.areaId, f.areaType, f.forecastMw, f.actualMw, f.temperatureF, f.humidityPct, f.confidenceLow, f.confidenceHigh]
      );
    }
    client.release();
  } catch (err) {
    logger.warn('DB persist error', { error: err.message });
  }

  // Publish to Kafka
  if (producer) {
    try {
      const messages = forecasts.map(f => ({
        key: f.areaId,
        value: JSON.stringify(f)
      }));
      await producer.send({ topic: 'demand.forecasts', messages });
    } catch (err) {
      logger.warn('Kafka publish error', { error: err.message });
    }
  }

  // Cache current forecast in Redis
  try {
    await redis.setex('forecast:current', 120, JSON.stringify(currentForecasts));
  } catch (err) { /* ignore */ }
}

// Background: regenerate forecasts every 60 seconds
async function startSimulation() {
  // Init Kafka producer
  try {
    producer = kafka.producer();
    await producer.connect();
    logger.info('Kafka producer connected');
  } catch (err) {
    logger.warn('Kafka not available', { error: err.message });
  }

  // Initial generation
  const initial = generateForecasts();
  await persistForecasts(initial);
  forecastHistory.push({ generatedAt: new Date().toISOString(), count: initial.length });
  logger.info('Initial forecast generated', { count: initial.length });

  // Periodic refresh
  setInterval(async () => {
    try {
      const forecasts = generateForecasts();
      await persistForecasts(forecasts);
      forecastHistory.push({ generatedAt: new Date().toISOString(), count: forecasts.length });
      if (forecastHistory.length > 60) forecastHistory.shift();
      logger.info('Forecast refreshed', { count: forecasts.length });
    } catch (err) {
      logger.error('Forecast error', { error: err.message });
    }
  }, 60000);
}

setTimeout(startSimulation, 15000);

// ============================================================
// API Endpoints
// ============================================================

// HTTP-triggered simulation cycle (for Dynatrace end-to-end tracing)
app.post('/api/forecast/simulate', async (req, res) => {
  forecastCycleCount++;
  logger.info('POST /api/forecast/simulate - triggering simulation cycle', { cycle: forecastCycleCount });

  // ~6% chance: simulate weather API timeout (forecast model depends on weather data)
  if (Math.random() < 0.06) {
    logger.error('Weather data provider timeout', {
      error: 'ETIMEDOUT: External weather API did not respond within 5000ms',
      provider: 'weather.utility.internal',
      cycle: forecastCycleCount
    });
    return res.status(504).json({ error: 'Weather data provider timeout - forecast cannot be generated' });
  }

  // ~4% chance: simulate numerical overflow in forecast model
  if (Math.random() < 0.04) {
    logger.error('Forecast model numerical instability', {
      error: 'NaN detected in load calculation for area SUB-003',
      area: 'SUB-003',
      temperatureF: -999,
      cycle: forecastCycleCount,
      stackTrace: 'at forecastLoad (index.js:88) -> tempFactor=Infinity'
    });
    return res.status(500).json({ error: 'Forecast model calculation error - numerical instability detected' });
  }

  try {
    const forecasts = generateForecasts();
    logger.debug('Forecasts generated', { count: forecasts.length, areas: areas.length, cycle: forecastCycleCount });
    await persistForecasts(forecasts);
    logger.debug('Forecasts persisted to DB and Kafka', { cycle: forecastCycleCount });
    forecastHistory.push({ generatedAt: new Date().toISOString(), count: forecasts.length });
    if (forecastHistory.length > 60) forecastHistory.shift();
    logger.info('Forecast refreshed via simulate', { count: forecasts.length });
    res.json({ status: 'Simulation cycle complete', forecastCount: forecasts.length, areas: areas.length });
  } catch (err) {
    logger.error('Forecast simulate error', { error: err.message });
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/forecast/current', (req, res) => {
  const areaId = req.query.areaId;
  let forecasts = currentForecasts;
  if (areaId) forecasts = forecasts.filter(f => f.areaId === areaId);

  // ~3% chance: Redis cache corruption simulation
  if (Math.random() < 0.03) {
    logger.error('Redis cache deserialization error', {
      error: 'SyntaxError: Unexpected token in JSON at position 0',
      key: 'forecast:current',
      action: 'falling back to in-memory data'
    });
  }

  logger.info('GET /api/forecast/current', { count: forecasts.length, areaId });
  logger.debug('Forecast data', { systemLoad: forecasts.find(f => f.areaId === 'SYSTEM' && f.hour === new Date().getHours())?.forecastMw });
  res.json(forecasts);
});

app.get('/api/forecast/hourly', (req, res) => {
  const hour = parseInt(req.query.hour);
  if (isNaN(hour) || hour < 0 || hour > 23) {
    return res.status(400).json({ error: 'Valid hour (0-23) required' });
  }
  const forecasts = currentForecasts.filter(f => f.hour === hour);
  res.json(forecasts);
});

app.get('/api/forecast/peak-demand', (req, res) => {
  // Find peak hour for each area
  const peaks = areas.map(area => {
    const areaForecasts = currentForecasts.filter(f => f.areaId === area.id);
    if (areaForecasts.length === 0) return null;
    const peak = areaForecasts.reduce((max, f) => f.forecastMw > max.forecastMw ? f : max);
    return {
      areaId: area.id,
      areaName: area.name,
      peakHour: peak.hour,
      peakForecastMw: peak.forecastMw,
      peakCapacityMw: area.peakCapacityMw,
      utilizationPct: peak.utilizationPct,
      temperature: peak.temperatureF
    };
  }).filter(Boolean);
  logger.info('GET /api/forecast/peak-demand');
  res.json(peaks);
});

app.get('/api/forecast/summary', (req, res) => {
  const systemForecasts = currentForecasts.filter(f => f.areaId === 'SYSTEM');
  const currentHour = new Date().getHours();
  const currentForecast = systemForecasts.find(f => f.hour === currentHour);
  const peakForecast = systemForecasts.reduce((max, f) => f.forecastMw > max.forecastMw ? f : max, systemForecasts[0] || {});

  res.json({
    currentLoadMw: currentForecast ? currentForecast.forecastMw : null,
    currentActualMw: currentForecast ? currentForecast.actualMw : null,
    peakForecastMw: peakForecast.forecastMw,
    peakHour: peakForecast.hour,
    systemCapacityMw: 1350,
    currentUtilizationPct: currentForecast ? currentForecast.utilizationPct : null,
    forecastGenerations: forecastHistory.length,
    lastGenerated: forecastHistory.length > 0 ? forecastHistory[forecastHistory.length - 1].generatedAt : null
  });
});

app.get('/api/forecast/areas', (req, res) => {
  res.json(areas);
});

app.get('/api/forecast/health', (req, res) => {
  res.json({
    status: 'Healthy',
    service: 'DemandForecastService',
    currentForecasts: currentForecasts.length,
    areas: areas.length
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => logger.info(`Demand Forecast Service running on port ${port}`));
