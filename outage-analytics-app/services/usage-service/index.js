const express = require('express');
const { Kafka } = require('kafkajs');
const Redis = require('ioredis');
const logger = require('./logger');

const app = express();
app.use(express.json());

const kafka = new Kafka({ clientId: 'usage-service', brokers: [(process.env.KAFKA_BROKER || 'kafka:9092')] });
let consumer = null;

const redis = new Redis({ host: process.env.REDIS_HOST || 'redis', port: 6379, retryStrategy: (t) => Math.min(t * 100, 3000) });
redis.on('error', () => {});

// ============================================================
// Sporadic error injection & request logging
// Includes togglable high-failure mode for Dynatrace problem detection
// ============================================================
let usageRequestCount = 0;
let usageFaultMode = false;

app.post('/api/usage/fault/enable', (req, res) => {
  usageFaultMode = true;
  logger.error('🔴 USAGE SERVICE FAULT MODE ENABLED — Redis + data pipeline errors will spike');
  res.json({ status: 'Fault mode ENABLED', service: 'usage-service' });
});
app.post('/api/usage/fault/disable', (req, res) => {
  usageFaultMode = false;
  logger.info('🟢 USAGE SERVICE FAULT MODE DISABLED');
  res.json({ status: 'Fault mode DISABLED', service: 'usage-service' });
});

app.use((req, res, next) => {
  usageRequestCount++;
  const start = Date.now();
  logger.debug('Incoming request', { method: req.method, path: req.path, requestId: usageRequestCount });

  res.on('finish', () => {
    const duration = Date.now() - start;
    const meta = { method: req.method, path: req.path, status: res.statusCode, durationMs: duration };
    if (res.statusCode >= 500) {
      logger.error('Usage request failed', meta);
    } else {
      logger.debug('Request completed', meta);
    }
  });

  // Fault mode: 70% of non-health/non-fault requests return Redis/pipeline error
  if (usageFaultMode && !req.path.includes('/health') && !req.path.includes('/fault/') && Math.random() < 0.70) {
    const cacheErrors = [
      'Error: connect ECONNREFUSED 10.0.0.8:6379 — Redis connection pool exhausted',
      'ReplyError: OOM command not allowed when used memory > maxmemory — Redis eviction failed',
      'Error: Kafka consumer disconnected — usage event stream interrupted, lag: 45000 messages',
      'AbortError: Redis connection lost — socket closed unexpectedly during pipeline flush'
    ];
    const errMsg = cacheErrors[Math.floor(Math.random() * cacheErrors.length)];
    logger.error('CACHE/PIPELINE FAILURE in usage-service', {
      error: errMsg,
      path: req.path,
      redisStatus: 'disconnected',
      kafkaLag: Math.floor(Math.random() * 50000)
    });
    return res.status(500).json({ error: errMsg, service: 'usage-service', timestamp: new Date().toISOString() });
  }

  next();
});

const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
let readingCounter = 1;
const usage = [];

function generateReading(customerId, meterNumber, timestamp) {
  const isIndustrial = [4,8,14,20,28,30].includes(customerId);
  const isCommercial = [2,6,10,12,15,18,22,26].includes(customerId);
  const baseUsage = isIndustrial ? 400 + Math.random() * 200 : isCommercial ? 80 + Math.random() * 60 : 15 + Math.random() * 25;
  const date = new Date(timestamp);
  const hour = date.getHours();
  const isWeekday = date.getDay() >= 1 && date.getDay() <= 5;
  const seasonFactor = Math.abs(date.getMonth() - 6) < 3 ? 1.3 : 1.0;
  const usageKwh = Math.round((baseUsage * seasonFactor + (Math.random() - 0.5) * 10) * 10) / 10;
  const onPeakRatio = (hour >= 8 && hour <= 20 && isWeekday) ? 0.6 : 0.3;
  const onPeak = Math.round(usageKwh * onPeakRatio * 10) / 10;
  const offPeak = Math.round((usageKwh - onPeak) * 10) / 10;
  return {
    id: `USG-${String(readingCounter++).padStart(4, '0')}`,
    customerId: `ACCT-${10000 + customerId}`, meterNumber,
    timestamp: date.toISOString(), usageKWh: usageKwh,
    peakKW: Math.round((usageKwh * 0.15 + Math.random() * 3) * 10) / 10,
    offPeakKWh: offPeak, onPeakKWh: onPeak,
    temperatureF: Math.round(45 + Math.random() * 40),
    dayOfWeek: days[date.getDay()],
    source: 'local'
  };
}

// Seed 7 days
for (let daysAgo = 6; daysAgo >= 0; daysAgo--) {
  const ts = Date.now() - daysAgo * 86400000;
  for (let cid = 1; cid <= 30; cid++) usage.push(generateReading(cid, `MTR-${20000 + cid}`, ts));
}

// Consume validated meter readings from Kafka (from meter-data-service)
async function startKafkaConsumer() {
  try {
    consumer = kafka.consumer({ groupId: 'usage-service-group' });
    await consumer.connect();
    await consumer.subscribe({ topic: 'meter.readings.validated', fromBeginning: false });
    await consumer.run({
      eachMessage: async ({ message }) => {
        try {
          const data = JSON.parse(message.value.toString());
          usage.push({
            id: `USG-${String(readingCounter++).padStart(4, '0')}`,
            customerId: data.customerId, meterNumber: data.meterId,
            timestamp: data.time, usageKWh: data.readingKwh,
            peakKW: data.demandKw, offPeakKWh: Math.round(data.readingKwh * 0.4 * 10) / 10,
            onPeakKWh: Math.round(data.readingKwh * 0.6 * 10) / 10,
            temperatureF: Math.round(45 + Math.random() * 40),
            dayOfWeek: days[new Date(data.time).getDay()],
            voltageV: data.voltageV, powerFactor: data.powerFactor,
            qualityFlag: data.qualityFlag, source: 'MDMS'
          });
          if (usage.length > 1000) usage.splice(0, usage.length - 1000);
        } catch (err) { logger.error('Kafka message error', { error: err.message }); }
      }
    });
    logger.info('Kafka consumer started for meter.readings.validated');
  } catch (err) { logger.warn('Kafka consumer unavailable', { error: err.message }); }
}

setTimeout(startKafkaConsumer, 20000);

// Background simulator (for local readings when no MDMS data flowing)
setInterval(() => {
  const cid = 1 + Math.floor(Math.random() * 30);
  const reading = generateReading(cid, `MTR-${20000 + cid}`, Date.now());
  usage.push(reading);
  logger.info('Local reading', { id: reading.id, customer: reading.customerId });
  if (usage.length > 1000) usage.splice(0, usage.length - 1000);
}, 30000 + Math.floor(Math.random() * 60000));

// HTTP-triggered simulation cycle (for Dynatrace end-to-end tracing)
app.post('/api/usage/simulate', async (req, res) => {
  logger.info('POST /api/usage/simulate - triggering simulation cycle');

  // ~7% chance: simulate Redis connection failure
  if (Math.random() < 0.07) {
    logger.error('Redis connection refused during usage caching', {
      error: 'ECONNREFUSED: Connection refused to redis:6379',
      operation: 'SETEX',
      key: 'usage:latest:*'
    });
    // Continue without cache - degraded mode
    logger.warn('Running in degraded mode - Redis unavailable, skipping cache update');
  }

  // ~5% chance: simulate memory pressure warning
  const memUsage = process.memoryUsage();
  if (Math.random() < 0.05) {
    logger.warn('Memory pressure detected in usage-service', {
      heapUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024),
      heapTotalMB: Math.round(memUsage.heapTotal / 1024 / 1024),
      rssMB: Math.round(memUsage.rss / 1024 / 1024),
      readingsInMemory: usage.length,
      threshold: '80%'
    });
  }

  const cid = 1 + Math.floor(Math.random() * 30);
  const reading = generateReading(cid, `MTR-${20000 + cid}`, Date.now());
  usage.push(reading);

  logger.debug('Usage reading generated', { id: reading.id, customerId: reading.customerId, usageKWh: reading.usageKWh, peakKW: reading.peakKW });

  // Cache latest reading in Redis
  try {
    await redis.setex(`usage:latest:${reading.customerId}`, 300, JSON.stringify(reading));
  } catch (err) { /* ignore */ }

  if (usage.length > 1000) usage.splice(0, usage.length - 1000);
  logger.info('Usage reading via simulate', { id: reading.id, customer: reading.customerId });
  res.json({ status: 'Simulation cycle complete', readingId: reading.id, customerId: reading.customerId, usageKWh: reading.usageKWh, totalReadings: usage.length });
});

app.get('/api/usage', (req, res) => { logger.info('GET /api/usage', { count: usage.length }); res.json(usage); });
app.get('/api/usage/customer/:customerId', (req, res) => {
  const r = usage.filter(u => u.customerId === req.params.customerId);
  res.json(r);
});
app.get('/api/usage/summary', (req, res) => {
  // ~4% chance: simulate data aggregation error
  if (Math.random() < 0.04) {
    logger.error('Data aggregation error in usage summary', {
      error: 'TypeError: Cannot read properties of undefined (reading \'usageKWh\')',
      readingCount: usage.length,
      corruptedIndex: Math.floor(Math.random() * usage.length)
    });
    return res.status(500).json({ error: 'Data aggregation failed - corrupted reading detected' });
  }

  const totalKWh = usage.reduce((s, u) => s + u.usageKWh, 0);
  const uniqueCustomers = new Set(usage.map(u => u.customerId)).size;
  const mdmsCount = usage.filter(u => u.source === 'MDMS').length;
  logger.info('GET /api/usage/summary', { totalReadings: usage.length, totalKWh: Math.round(totalKWh), uniqueCustomers });
  logger.debug('Usage breakdown', { mdmsReadings: mdmsCount, localReadings: usage.length - mdmsCount, avgKWh: Math.round(totalKWh / (usage.length || 1)) });
  res.json({ totalReadings: usage.length, totalKWh: Math.round(totalKWh * 10) / 10, uniqueCustomers, avgKWh: Math.round(totalKWh / (usage.length || 1) * 10) / 10, mdmsReadings: mdmsCount, localReadings: usage.length - mdmsCount });
});
app.post('/api/usage', (req, res) => { const r = { id: `USG-${String(readingCounter++).padStart(4, '0')}`, ...req.body }; usage.push(r); res.status(201).json(r); });
app.get('/api/usage/health', (req, res) => { res.json({ status: 'Healthy', service: 'UsageService', readingCount: usage.length, kafkaConnected: !!consumer }); });

const port = process.env.PORT || 3000;
app.listen(port, () => logger.info(`Usage Service running on port ${port}`));
