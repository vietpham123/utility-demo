const express = require('express');
const { Pool } = require('pg');
const { Kafka } = require('kafkajs');
const axios = require('axios');
const logger = require('./logger');

const app = express();
app.use(express.json());

const pool = new Pool({
  host: process.env.DB_HOST || 'timescaledb',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'utilitydb',
  user: process.env.DB_USER || 'utilityuser',
  password: process.env.DB_PASSWORD || 'utility2026!',
  max: 10
});

const kafka = new Kafka({
  clientId: 'outage-service',
  brokers: [(process.env.KAFKA_BROKER || 'kafka:9092')]
});
let producer = null;
let consumer = null;

const GRID_SERVICE_URL = process.env.GRID_SERVICE_URL || 'http://grid-topology-service:3000';

// ============================================================
// Sporadic error injection & request logging
// ============================================================
let requestCount = 0;
let errorCount = 0;

app.use((req, res, next) => {
  requestCount++;
  const start = Date.now();
  logger.debug('Incoming request', { method: req.method, path: req.path, requestId: requestCount });

  res.on('finish', () => {
    const duration = Date.now() - start;
    const meta = { method: req.method, path: req.path, status: res.statusCode, durationMs: duration };
    if (res.statusCode >= 500) {
      errorCount++;
      logger.error('Request failed', { ...meta, totalErrors: errorCount });
    } else if (duration > 2000) {
      logger.warn('Slow outage query detected', meta);
    } else {
      logger.debug('Request completed', meta);
    }
  });
  next();
});

const locations = [
  { city: 'Chicago, IL', lat: 41.8781, lng: -87.6298 },
  { city: 'Baltimore, MD', lat: 39.2904, lng: -76.6122 },
  { city: 'Philadelphia, PA', lat: 39.9526, lng: -75.1652 },
  { city: 'Washington, DC', lat: 38.9072, lng: -77.0369 },
  { city: 'Atlantic City, NJ', lat: 39.3643, lng: -74.4229 },
  { city: 'Wilmington, DE', lat: 39.7391, lng: -75.5398 },
  { city: 'Cherry Hill, NJ', lat: 39.9348, lng: -75.0307 },
  { city: 'Chester, PA', lat: 39.8496, lng: -75.3557 },
  { city: 'Ventnor City, NJ', lat: 39.3404, lng: -74.4774 }
];

const causes = [
  'Transformer failure', 'Severe weather - ice storm', 'Vehicle accident - downed line',
  'Underground cable fault', 'Equipment overload', 'Planned maintenance',
  'Tree contact with power line', 'Substation relay trip', 'Lightning strike',
  'Aging infrastructure failure', 'Animal contact', 'Construction damage'
];

const crews = [
  'Crew-Alpha-7', 'Crew-Beta-3', 'Crew-Delta-1', 'Crew-Gamma-5',
  'Crew-Echo-2', 'Crew-Foxtrot-4', 'Crew-Hotel-6', 'Crew-India-8'
];

const priorities = ['Critical', 'High', 'Medium', 'Low'];
const equipmentTypes = ['Substation', 'Feeder', 'Transformer'];

let outageCounter = 1;
const outages = [];

function generateOutage(daysAgo, resolved) {
  const loc = locations[Math.floor(Math.random() * locations.length)];
  const start = new Date(Date.now() - daysAgo * 86400000 + Math.random() * 86400000);
  const end = resolved ? new Date(start.getTime() + (2 + Math.random() * 22) * 3600000) : null;
  const id = `OUT-${String(outageCounter++).padStart(3, '0')}`;
  const priority = priorities[Math.floor(Math.random() * priorities.length)];
  const affected = priority === 'Critical' ? 2000 + Math.floor(Math.random() * 5000) :
                   priority === 'High' ? 500 + Math.floor(Math.random() * 2000) :
                   priority === 'Medium' ? 100 + Math.floor(Math.random() * 500) :
                   20 + Math.floor(Math.random() * 100);
  const eqType = equipmentTypes[Math.floor(Math.random() * equipmentTypes.length)];
  const eqId = eqType === 'Substation' ? Math.ceil(Math.random() * 3) :
               eqType === 'Feeder' ? Math.ceil(Math.random() * 12) :
               Math.ceil(Math.random() * 36);

  return {
    id, location: loc.city,
    latitude: loc.lat + (Math.random() - 0.5) * 0.05,
    longitude: loc.lng + (Math.random() - 0.5) * 0.05,
    startTime: start.toISOString(),
    endTime: end ? end.toISOString() : null,
    status: resolved ? 'Resolved' : (Math.random() > 0.7 ? 'Investigating' : 'Active'),
    cause: causes[Math.floor(Math.random() * causes.length)],
    affectedCustomers: affected,
    estimatedRestoration: !resolved ? new Date(Date.now() + (4 + Math.random() * 48) * 3600000).toISOString() : null,
    crewAssigned: crews[Math.floor(Math.random() * crews.length)],
    priority, equipmentType: eqType, equipmentId: eqId, source: 'OMS'
  };
}

async function publishOutageEvent(outage) {
  if (!producer) return;
  try {
    await producer.send({ topic: 'outage.events', messages: [{ key: outage.id, value: JSON.stringify(outage) }] });
  } catch (err) { logger.warn('Kafka publish error', { error: err.message }); }
}

async function seedOutages() {
  for (let i = 0; i < 8; i++) outages.push(generateOutage(2 + Math.floor(Math.random() * 14), true));
  for (let i = 0; i < 4; i++) outages.push(generateOutage(Math.random() * 2, false));
  try {
    const client = await pool.connect();
    for (const o of outages) {
      await client.query(`
        INSERT INTO outages.outage_records (id, equipment_type, equipment_id, location, latitude, longitude,
          start_time, end_time, status, cause, customers_affected, priority, crew_assigned, estimated_restoration)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14) ON CONFLICT (id) DO NOTHING
      `, [o.id, o.equipmentType, o.equipmentId, o.location, o.latitude, o.longitude,
          o.startTime, o.endTime, o.status, o.cause, o.affectedCustomers, o.priority,
          o.crewAssigned, o.estimatedRestoration]);
    }
    client.release();
    logger.info('Seeded outages to database', { count: outages.length });
  } catch (err) { logger.warn('DB seed error', { error: err.message }); }
}

async function startKafkaConsumer() {
  try {
    consumer = kafka.consumer({ groupId: 'outage-service-group' });
    await consumer.connect();
    await consumer.subscribe({ topics: ['scada.alerts', 'meter.anomalies'], fromBeginning: false });
    await consumer.run({
      eachMessage: async ({ topic, message }) => {
        try {
          const data = JSON.parse(message.value.toString());
          if (topic === 'scada.alerts' && (data.Severity === 'High' || data.severity === 'High')) {
            const eqType = data.EquipmentType || data.equipmentType;
            const eqId = data.EquipmentId || data.equipmentId;
            const existing = outages.find(o => o.status !== 'Resolved' && o.equipmentType === eqType && o.equipmentId === eqId);
            if (!existing && Math.random() > 0.7) {
              const newOutage = {
                id: `OUT-${String(outageCounter++).padStart(3, '0')}`,
                location: locations[Math.floor(Math.random() * locations.length)].city,
                latitude: locations[0].lat + (Math.random() - 0.5) * 0.1,
                longitude: locations[0].lng + (Math.random() - 0.5) * 0.1,
                startTime: new Date().toISOString(), endTime: null, status: 'Active',
                cause: data.AlertType || data.alertType || 'Equipment anomaly detected',
                affectedCustomers: 50 + Math.floor(Math.random() * 500),
                estimatedRestoration: new Date(Date.now() + (2 + Math.random() * 12) * 3600000).toISOString(),
                crewAssigned: crews[Math.floor(Math.random() * crews.length)],
                priority: 'High', equipmentType: eqType, equipmentId: eqId, source: 'SCADA-Auto-Detect'
              };
              outages.push(newOutage);
              await publishOutageEvent(newOutage);
              logger.info('SCADA-triggered outage', { id: newOutage.id });
            }
          }
        } catch (err) { logger.error('Kafka message error', { error: err.message }); }
      }
    });
    logger.info('Kafka consumer started');
  } catch (err) { logger.warn('Kafka consumer unavailable', { error: err.message }); }
}

(async () => {
  await seedOutages();
  try {
    producer = kafka.producer();
    await producer.connect();
    for (const o of outages) await publishOutageEvent(o);
    logger.info('Kafka producer connected');
  } catch (err) { logger.warn('Kafka producer unavailable', { error: err.message }); }
  await startKafkaConsumer();
})();

// Background simulator
setInterval(async () => {
  const active = outages.filter(o => o.status !== 'Resolved');
  if (active.length > 0 && Math.random() > 0.5) {
    const idx = Math.floor(Math.random() * active.length);
    active[idx].status = 'Resolved';
    active[idx].endTime = new Date().toISOString();
    active[idx].estimatedRestoration = null;
    await publishOutageEvent(active[idx]);
    try { await pool.query('UPDATE outages.outage_records SET status=$1, end_time=$2 WHERE id=$3', ['Resolved', active[idx].endTime, active[idx].id]); } catch (e) {}
    logger.info('Resolved outage', { id: active[idx].id });
  }
  if (Math.random() > 0.4) {
    const newOutage = generateOutage(0, false);
    outages.push(newOutage);
    await publishOutageEvent(newOutage);
    try {
      await pool.query(`INSERT INTO outages.outage_records (id,equipment_type,equipment_id,location,latitude,longitude,start_time,status,cause,customers_affected,priority,crew_assigned,estimated_restoration) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)`,
        [newOutage.id, newOutage.equipmentType, newOutage.equipmentId, newOutage.location, newOutage.latitude, newOutage.longitude, newOutage.startTime, newOutage.status, newOutage.cause, newOutage.affectedCustomers, newOutage.priority, newOutage.crewAssigned, newOutage.estimatedRestoration]);
    } catch (e) {}
    logger.info('New outage', { id: newOutage.id, source: newOutage.source });
  }
  if (outages.length > 200) outages.splice(0, outages.length - 200);
}, 60000 + Math.floor(Math.random() * 60000));

// HTTP-triggered simulation cycle (for Dynatrace end-to-end tracing)
app.post('/api/outages/simulate', async (req, res) => {
  logger.info('POST /api/outages/simulate - triggering simulation cycle');
  const results = { resolved: 0, created: 0 };

  // ~8% chance: simulate database connection pool exhaustion
  if (Math.random() < 0.08) {
    logger.error('Database connection pool exhausted', {
      error: 'TimeoutError: Unable to acquire connection from pool',
      pool: { total: 10, idle: 0, waiting: 3 },
      service: 'outage-service'
    });
    return res.status(503).json({ error: 'Database connection pool exhausted - all connections in use' });
  }

  // ~5% chance: simulate Kafka producer disconnect
  if (Math.random() < 0.05) {
    logger.error('Kafka producer disconnected during simulation', {
      error: 'KafkaJSNumberOfRetriesExceeded: Broker not available',
      broker: process.env.KAFKA_BROKER || 'kafka:9092',
      topic: 'outage.events'
    });
    // Continue processing but log the error - partial failure
  }

  // Resolve an active outage
  const active = outages.filter(o => o.status !== 'Resolved');
  if (active.length > 0 && Math.random() > 0.5) {
    const idx = Math.floor(Math.random() * active.length);
    active[idx].status = 'Resolved';
    active[idx].endTime = new Date().toISOString();
    active[idx].estimatedRestoration = null;
    await publishOutageEvent(active[idx]);
    try { await pool.query('UPDATE outages.outage_records SET status=$1, end_time=$2 WHERE id=$3', ['Resolved', active[idx].endTime, active[idx].id]); } catch (e) {}
    results.resolved = 1;
    logger.info('Resolved outage via simulate', { id: active[idx].id });
  }

  // Create a new outage with grid topology lookup
  if (Math.random() > 0.4) {
    const newOutage = generateOutage(0, false);

    // Cross-service call: lookup affected customers from grid-topology-service
    try {
      const { data } = await axios.get(`${GRID_SERVICE_URL}/api/grid/affected-customers/${newOutage.equipmentType}/${newOutage.equipmentId}`, { timeout: 3000 });
      if (data && data.affectedCustomers) {
        newOutage.affectedCustomers = data.affectedCustomers;
      }
    } catch (err) {
      logger.warn('Grid topology lookup failed, using estimate', { error: err.message });
    }

    outages.push(newOutage);
    await publishOutageEvent(newOutage);
    try {
      await pool.query(`INSERT INTO outages.outage_records (id,equipment_type,equipment_id,location,latitude,longitude,start_time,status,cause,customers_affected,priority,crew_assigned,estimated_restoration) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)`,
        [newOutage.id, newOutage.equipmentType, newOutage.equipmentId, newOutage.location, newOutage.latitude, newOutage.longitude, newOutage.startTime, newOutage.status, newOutage.cause, newOutage.affectedCustomers, newOutage.priority, newOutage.crewAssigned, newOutage.estimatedRestoration]);
    } catch (e) {}
    results.created = 1;
    logger.info('New outage via simulate', { id: newOutage.id });
  }

  if (outages.length > 200) outages.splice(0, outages.length - 200);
  res.json({ status: 'Simulation cycle complete', ...results, totalOutages: outages.length, activeOutages: outages.filter(o => o.status !== 'Resolved').length });
});

app.get('/api/outages', (req, res) => {
  // ~3% chance: simulate slow DB query
  if (Math.random() < 0.03) {
    const delay = 3000 + Math.floor(Math.random() * 4000);
    logger.warn('Slow database query for outage list', { delayMs: delay, outageCount: outages.length });
    return setTimeout(() => {
      logger.info('GET /api/outages (delayed)', { count: outages.length, delayMs: delay });
      res.json(outages);
    }, delay);
  }
  logger.info('GET /api/outages', { count: outages.length });
  logger.debug('Outage breakdown', { active: outages.filter(o => o.status !== 'Resolved').length, resolved: outages.filter(o => o.status === 'Resolved').length });
  res.json(outages);
});
app.get('/api/outages/active', (req, res) => {
  const a = outages.filter(o => o.status !== 'Resolved');
  logger.info('GET /api/outages/active', { count: a.length });
  logger.debug('Active outages by priority', { critical: a.filter(o => o.priority === 'Critical').length, high: a.filter(o => o.priority === 'High').length, medium: a.filter(o => o.priority === 'Medium').length });
  res.json(a);
});
app.get('/api/outages/health', (req, res) => { res.json({ status: 'Healthy', service: 'OutageService', outageCount: outages.length, activeCount: outages.filter(o => o.status !== 'Resolved').length }); });
app.get('/api/outages/stats/summary', (req, res) => {
  const active = outages.filter(o => o.status !== 'Resolved');
  const byPriority = {}; active.forEach(o => { byPriority[o.priority] = (byPriority[o.priority] || 0) + 1; });
  const byCause = {}; outages.forEach(o => { byCause[o.cause] = (byCause[o.cause] || 0) + 1; });
  res.json({ totalOutages: outages.length, activeOutages: active.length, resolvedOutages: outages.length - active.length, totalAffectedCustomers: active.reduce((s,o) => s + (o.affectedCustomers||0), 0), byPriority, topCauses: Object.entries(byCause).sort((a,b) => b[1]-a[1]).slice(0,5) });
});
app.get('/api/outages/:id', (req, res) => { const o = outages.find(o => o.id === req.params.id); if (!o) return res.status(404).json({ error: 'Not found' }); res.json(o); });
app.post('/api/outages', async (req, res) => { const o = { id: `OUT-${String(outageCounter++).padStart(3, '0')}`, ...req.body, source: 'Manual' }; outages.push(o); await publishOutageEvent(o); res.status(201).json(o); });

const port = process.env.PORT || 3000;
app.listen(port, () => logger.info(`Outage Service running on port ${port}`));
