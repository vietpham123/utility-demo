const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const { Kafka } = require('kafkajs');
const http = require('http');
const logger = require('./logger');

const app = express();
app.use(express.json());

const SCADA_SERVICE_URL = process.env.SCADA_SERVICE_URL || 'http://scada-service:8080';

const pool = new Pool({
  host: process.env.DB_HOST || 'timescaledb',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'utilitydb',
  user: process.env.DB_USER || 'utilityuser',
  password: process.env.DB_PASSWORD || process.env.DB_PASSWORD,
  max: 10,
  idleTimeoutMillis: 30000
});

const redis = new Redis({
  host: process.env.REDIS_HOST || 'redis',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times) => Math.min(times * 100, 3000)
});

redis.on('error', (err) => logger.warn('Redis connection error', { error: err.message }));

const CACHE_TTL = 30; // seconds

// ============================================================
// Sporadic error injection & request logging
// ============================================================
app.use((req, res, next) => {
  const start = Date.now();
  logger.debug('Incoming request', { method: req.method, path: req.path });

  res.on('finish', () => {
    const duration = Date.now() - start;
    const meta = { method: req.method, path: req.path, status: res.statusCode, durationMs: duration };
    if (res.statusCode >= 500) {
      logger.error('Grid topology request failed', meta);
    } else if (duration > 2000) {
      logger.warn('Slow grid query', meta);
    } else {
      logger.debug('Request completed', meta);
    }
  });

  // ~3% chance: simulate slow PostgreSQL full table scan
  if (Math.random() < 0.03 && req.path.includes('/topology')) {
    const delay = 4000 + Math.floor(Math.random() * 3000);
    logger.warn('Slow topology query - possible sequential scan detected', {
      path: req.path,
      estimatedDelayMs: delay,
      hint: 'Consider adding index on grid.feeders(substation_id)'
    });
    return setTimeout(() => next(), delay);
  }

  next();
});

// ============================================================
// Substations
// ============================================================
app.get('/api/grid/substations', async (req, res) => {
  try {
    const cached = await redis.get('grid:substations').catch(() => null);
    if (cached) { return res.json(JSON.parse(cached)); }
    const { rows } = await pool.query('SELECT * FROM grid.substations ORDER BY id');
    await redis.setex('grid:substations', CACHE_TTL, JSON.stringify(rows)).catch(() => {});
    logger.info('GET /api/grid/substations', { count: rows.length });
    res.json(rows);
  } catch (err) {
    logger.error('Error fetching substations', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/api/grid/substations/:id', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM grid.substations WHERE id = $1', [req.params.id]);
    if (rows.length === 0) return res.status(404).json({ error: 'Substation not found' });
    res.json(rows[0]);
  } catch (err) {
    logger.error('Error fetching substation', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Feeders
// ============================================================
app.get('/api/grid/feeders', async (req, res) => {
  try {
    const cached = await redis.get('grid:feeders').catch(() => null);
    if (cached) { return res.json(JSON.parse(cached)); }
    const { rows } = await pool.query(`
      SELECT f.*, s.name as substation_name, s.code as substation_code
      FROM grid.feeders f JOIN grid.substations s ON f.substation_id = s.id
      ORDER BY f.id
    `);
    await redis.setex('grid:feeders', CACHE_TTL, JSON.stringify(rows)).catch(() => {});
    logger.info('GET /api/grid/feeders', { count: rows.length });
    res.json(rows);
  } catch (err) {
    logger.error('Error fetching feeders', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/api/grid/feeders/substation/:substationId', async (req, res) => {
  try {
    const { rows } = await pool.query(
      'SELECT * FROM grid.feeders WHERE substation_id = $1 ORDER BY id',
      [req.params.substationId]
    );
    res.json(rows);
  } catch (err) {
    logger.error('Error fetching feeders by substation', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Transformers
// ============================================================
app.get('/api/grid/transformers', async (req, res) => {
  try {
    const cached = await redis.get('grid:transformers').catch(() => null);
    if (cached) { return res.json(JSON.parse(cached)); }
    const { rows } = await pool.query(`
      SELECT t.*, f.name as feeder_name, f.code as feeder_code, s.name as substation_name
      FROM grid.transformers t
      JOIN grid.feeders f ON t.feeder_id = f.id
      JOIN grid.substations s ON f.substation_id = s.id
      ORDER BY t.id
    `);
    await redis.setex('grid:transformers', CACHE_TTL, JSON.stringify(rows)).catch(() => {});
    logger.info('GET /api/grid/transformers', { count: rows.length });
    res.json(rows);
  } catch (err) {
    logger.error('Error fetching transformers', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Service Points
// ============================================================
app.get('/api/grid/service-points', async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT sp.*, t.name as transformer_name, t.code as transformer_code,
             f.name as feeder_name, s.name as substation_name
      FROM grid.service_points sp
      JOIN grid.transformers t ON sp.transformer_id = t.id
      JOIN grid.feeders f ON t.feeder_id = f.id
      JOIN grid.substations s ON f.substation_id = s.id
      ORDER BY sp.id
    `);
    logger.info('GET /api/grid/service-points', { count: rows.length });
    res.json(rows);
  } catch (err) {
    logger.error('Error fetching service points', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Topology: Full graph from substation down to service points
// ============================================================
app.get('/api/grid/topology', async (req, res) => {
  try {
    const cached = await redis.get('grid:topology').catch(() => null);
    if (cached) { return res.json(JSON.parse(cached)); }

    const [subs, fdrs, trxs, sps] = await Promise.all([
      pool.query('SELECT * FROM grid.substations'),
      pool.query('SELECT * FROM grid.feeders'),
      pool.query('SELECT * FROM grid.transformers'),
      pool.query('SELECT * FROM grid.service_points')
    ]);

    const topology = subs.rows.map(sub => ({
      ...sub,
      feeders: fdrs.rows.filter(f => f.substation_id === sub.id).map(fdr => ({
        ...fdr,
        transformers: trxs.rows.filter(t => t.feeder_id === fdr.id).map(trx => ({
          ...trx,
          servicePoints: sps.rows.filter(sp => sp.transformer_id === trx.id)
        }))
      }))
    }));

    await redis.setex('grid:topology', CACHE_TTL, JSON.stringify(topology)).catch(() => {});
    logger.info('GET /api/grid/topology', { substations: topology.length });
    res.json(topology);
  } catch (err) {
    logger.error('Error building topology', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Affected Customers: given equipment failure, who is impacted?
// ============================================================
app.get('/api/grid/affected-customers/:equipmentType/:equipmentId', async (req, res) => {
  try {
    const { equipmentType, equipmentId } = req.params;
    let query;

    if (equipmentType === 'substation') {
      query = `
        SELECT sp.customer_id, sp.meter_id, sp.address, sp.service_type,
               t.name as transformer, f.name as feeder, s.name as substation
        FROM grid.service_points sp
        JOIN grid.transformers t ON sp.transformer_id = t.id
        JOIN grid.feeders f ON t.feeder_id = f.id
        JOIN grid.substations s ON f.substation_id = s.id
        WHERE s.id = $1
      `;
    } else if (equipmentType === 'feeder') {
      query = `
        SELECT sp.customer_id, sp.meter_id, sp.address, sp.service_type,
               t.name as transformer, f.name as feeder
        FROM grid.service_points sp
        JOIN grid.transformers t ON sp.transformer_id = t.id
        JOIN grid.feeders f ON t.feeder_id = f.id
        WHERE f.id = $1
      `;
    } else if (equipmentType === 'transformer') {
      query = `
        SELECT sp.customer_id, sp.meter_id, sp.address, sp.service_type,
               t.name as transformer
        FROM grid.service_points sp
        JOIN grid.transformers t ON sp.transformer_id = t.id
        WHERE t.id = $1
      `;
    } else {
      return res.status(400).json({ error: 'Invalid equipment type. Use: substation, feeder, or transformer' });
    }

    const { rows } = await pool.query(query, [equipmentId]);
    logger.info('GET /api/grid/affected-customers', { equipmentType, equipmentId, affected: rows.length });
    res.json({ equipmentType, equipmentId: parseInt(equipmentId), affectedCustomers: rows.length, customers: rows });
  } catch (err) {
    logger.error('Error finding affected customers', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

// ============================================================
// Grid Stats Summary
// ============================================================
app.get('/api/grid/stats', async (req, res) => {
  try {
    // ~5% chance: simulate query timeout on parallel aggregation
    if (Math.random() < 0.05) {
      logger.error('PostgreSQL query timeout on grid stats aggregation', {
        error: 'QueryCanceledError: canceling statement due to statement timeout',
        queries: ['substations COUNT(*)', 'feeders COUNT(*)', 'transformers COUNT(*)', 'service_points COUNT(*)'],
        timeoutMs: 5000
      });
      return res.status(503).json({ error: 'Database query timeout - grid stats temporarily unavailable' });
    }

    const cached = await redis.get('grid:stats').catch(() => null);
    if (cached) {
      logger.debug('Grid stats served from cache');
      return res.json(JSON.parse(cached));
    }
    const [subs, fdrs, trxs, sps] = await Promise.all([
      pool.query('SELECT COUNT(*) as count, SUM(capacity_mw) as total_capacity FROM grid.substations'),
      pool.query('SELECT COUNT(*) as count, SUM(length_miles) as total_miles FROM grid.feeders'),
      pool.query('SELECT COUNT(*) as count, SUM(capacity_kva) as total_capacity FROM grid.transformers'),
      pool.query('SELECT COUNT(*) as count FROM grid.service_points')
    ]);
    const stats = {
      substations: { count: parseInt(subs.rows[0].count), totalCapacityMW: parseFloat(subs.rows[0].total_capacity) },
      feeders: { count: parseInt(fdrs.rows[0].count), totalMiles: parseFloat(fdrs.rows[0].total_miles) },
      transformers: { count: parseInt(trxs.rows[0].count), totalCapacityKVA: parseFloat(trxs.rows[0].total_capacity) },
      servicePoints: { count: parseInt(sps.rows[0].count) }
    };

    // Enrich grid stats with live SCADA sensor data (adds PurePath depth)
    try {
      const scadaData = await new Promise((resolve, reject) => {
        const req = http.get(`${SCADA_SERVICE_URL}/api/scada/summary`, { timeout: 3000 }, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try { resolve(JSON.parse(data)); } catch (e) { resolve(null); }
          });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
      });
      if (scadaData) {
        stats.scadaSensors = scadaData.totalSensors || scadaData.sensorCount || 0;
        logger.info('Enriched grid stats with SCADA sensor data', { sensors: stats.scadaSensors });
      }
    } catch (err) {
      logger.warn('SCADA service enrichment failed (non-critical)', { error: err.message });
    }

    await redis.setex('grid:stats', CACHE_TTL, JSON.stringify(stats)).catch(() => {});
    logger.info('GET /api/grid/stats');
    res.json(stats);
  } catch (err) {
    logger.error('Error fetching grid stats', { error: err.message });
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/api/grid/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'Healthy', service: 'GridTopologyService', database: 'Connected' });
  } catch (err) {
    res.status(503).json({ status: 'Unhealthy', service: 'GridTopologyService', database: 'Disconnected' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => logger.info(`Grid Topology Service running on port ${port}`));
