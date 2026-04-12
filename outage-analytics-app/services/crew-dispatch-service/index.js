const express = require('express');
const { WebSocketServer } = require('ws');
const http = require('http');
const { Pool } = require('pg');
const amqp = require('amqplib');
const axios = require('axios');
const logger = require('./logger');

const app = express();
app.use(express.json());
const server = http.createServer(app);

// WebSocket server for real-time crew updates
const wss = new WebSocketServer({ server, path: '/ws/crew-updates' });

const pool = new Pool({
  host: process.env.DB_HOST || 'timescaledb',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'utilitydb',
  user: process.env.DB_USER || 'utilityuser',
  password: process.env.DB_PASSWORD || process.env.DB_PASSWORD,
  max: 10
});

const OUTAGE_URL = process.env.OUTAGE_SERVICE_URL || 'http://outage-service:3000';
const NOTIFICATION_URL = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:5001';
const RABBITMQ_URL = process.env.RABBITMQ_URL || process.env.RABBITMQ_URL;

// ============================================================
// Crew & Dispatch State
// ============================================================
const crews = [
  { id: 'CREW-001', name: 'Alpha Team', lead: 'Mike Torres', members: 4, vehicle: 'Bucket Truck A-7', region: 'Chicago-North', status: 'Available', skills: ['overhead', 'underground', 'transformer'], currentAssignment: null },
  { id: 'CREW-002', name: 'Beta Team', lead: 'Sarah Chen', members: 3, vehicle: 'Line Truck B-3', region: 'Chicago-South', status: 'Available', skills: ['overhead', 'tree-trimming'], currentAssignment: null },
  { id: 'CREW-003', name: 'Delta Team', lead: 'James Wilson', members: 5, vehicle: 'Bucket Truck D-1', region: 'Baltimore', status: 'Available', skills: ['overhead', 'underground', 'substation'], currentAssignment: null },
  { id: 'CREW-004', name: 'Gamma Team', lead: 'Lisa Park', members: 4, vehicle: 'Splice Van G-5', region: 'Philadelphia', status: 'Available', skills: ['underground', 'cable-splice'], currentAssignment: null },
  { id: 'CREW-005', name: 'Echo Team', lead: 'Robert Adams', members: 3, vehicle: 'Bucket Truck E-2', region: 'Washington-DC', status: 'Available', skills: ['overhead', 'transformer'], currentAssignment: null },
  { id: 'CREW-006', name: 'Foxtrot Team', lead: 'Maria Garcia', members: 4, vehicle: 'Line Truck F-4', region: 'Atlantic-City', status: 'Available', skills: ['overhead', 'underground', 'emergency'], currentAssignment: null },
  { id: 'CREW-007', name: 'Hotel Team', lead: 'David Kim', members: 3, vehicle: 'Bucket Truck H-6', region: 'Wilmington', status: 'Available', skills: ['overhead', 'substation'], currentAssignment: null },
  { id: 'CREW-008', name: 'India Team', lead: 'Amy Johnson', members: 5, vehicle: 'Emergency Response I-8', region: 'Cherry-Hill', status: 'Available', skills: ['overhead', 'underground', 'substation', 'emergency'], currentAssignment: null },
  { id: 'CREW-009', name: 'Juliet Team', lead: 'Carlos Rivera', members: 4, vehicle: 'Bucket Truck J-9', region: 'NewYork', status: 'Available', skills: ['overhead', 'underground', 'transformer'], currentAssignment: null },
  { id: 'CREW-010', name: 'Kilo Team', lead: 'Priya Sharma', members: 3, vehicle: 'Line Truck K-10', region: 'Boston', status: 'Available', skills: ['overhead', 'tree-trimming', 'cable-splice'], currentAssignment: null },
  { id: 'CREW-011', name: 'Lima Team', lead: 'Marcus Brown', members: 5, vehicle: 'Bucket Truck L-11', region: 'Atlanta', status: 'Available', skills: ['overhead', 'underground', 'substation'], currentAssignment: null },
  { id: 'CREW-012', name: 'Mike Team', lead: 'Jennifer Lee', members: 4, vehicle: 'Emergency Response M-12', region: 'Miami', status: 'Available', skills: ['overhead', 'underground', 'emergency'], currentAssignment: null },
  { id: 'CREW-013', name: 'November Team', lead: 'Kevin O\'Brien', members: 4, vehicle: 'Bucket Truck N-13', region: 'Dallas', status: 'Available', skills: ['overhead', 'transformer', 'substation'], currentAssignment: null },
  { id: 'CREW-014', name: 'Oscar Team', lead: 'Ana Morales', members: 3, vehicle: 'Line Truck O-14', region: 'Houston', status: 'Available', skills: ['underground', 'cable-splice', 'emergency'], currentAssignment: null },
  { id: 'CREW-015', name: 'Papa Team', lead: 'Derek Washington', members: 4, vehicle: 'Bucket Truck P-15', region: 'Nashville', status: 'Available', skills: ['overhead', 'underground', 'tree-trimming'], currentAssignment: null },
  { id: 'CREW-016', name: 'Quebec Team', lead: 'Susan Patel', members: 3, vehicle: 'Splice Van Q-16', region: 'Charlotte', status: 'Available', skills: ['underground', 'cable-splice'], currentAssignment: null },
  { id: 'CREW-017', name: 'Romeo Team', lead: 'Brian Foster', members: 4, vehicle: 'Bucket Truck R-17', region: 'Orlando', status: 'Available', skills: ['overhead', 'transformer', 'emergency'], currentAssignment: null },
  { id: 'CREW-018', name: 'Sierra Team', lead: 'Diana Scott', members: 5, vehicle: 'Emergency Response S-18', region: 'Detroit', status: 'Available', skills: ['overhead', 'underground', 'substation', 'emergency'], currentAssignment: null },
  { id: 'CREW-019', name: 'Tango Team', lead: 'Frank Miller', members: 3, vehicle: 'Line Truck T-19', region: 'Cleveland', status: 'Available', skills: ['overhead', 'tree-trimming'], currentAssignment: null },
  { id: 'CREW-020', name: 'Uniform Team', lead: 'Rachel Davis', members: 4, vehicle: 'Bucket Truck U-20', region: 'Pittsburgh', status: 'Available', skills: ['overhead', 'underground', 'transformer'], currentAssignment: null },
  { id: 'CREW-021', name: 'Victor Team', lead: 'Greg Anderson', members: 3, vehicle: 'Splice Van V-21', region: 'StLouis', status: 'Available', skills: ['underground', 'cable-splice', 'substation'], currentAssignment: null },
  { id: 'CREW-022', name: 'Whiskey Team', lead: 'Emily Thompson', members: 4, vehicle: 'Bucket Truck W-22', region: 'Minneapolis', status: 'Available', skills: ['overhead', 'underground', 'emergency'], currentAssignment: null }
];

const dispatchHistory = [];
let dispatchCounter = 0;
let requestCount = 0;
let errorCount = 0;

// RabbitMQ connection
let rabbitChannel = null;

async function connectRabbitMQ() {
  try {
    const conn = await amqp.connect(RABBITMQ_URL);
    rabbitChannel = conn.createChannel ? await conn.createChannel() : null;
    if (rabbitChannel) {
      await rabbitChannel.assertExchange('crew.events', 'topic', { durable: true });
      await rabbitChannel.assertQueue('crew.dispatch', { durable: true });
      await rabbitChannel.assertQueue('crew.status-updates', { durable: true });
      await rabbitChannel.bindQueue('crew.dispatch', 'crew.events', 'crew.dispatched');
      await rabbitChannel.bindQueue('crew.status-updates', 'crew.events', 'crew.status.*');
      logger.info('RabbitMQ connected - crew exchanges and queues ready');
    }
  } catch (err) {
    logger.warn('RabbitMQ not available, running without message broker', { error: err.message });
  }
}

function publishCrewEvent(routingKey, data) {
  if (!rabbitChannel) return;
  try {
    rabbitChannel.publish('crew.events', routingKey, Buffer.from(JSON.stringify(data)), { persistent: true });
    logger.debug('Published crew event', { routingKey, dispatchId: data.dispatchId });
  } catch (err) {
    logger.error('Failed to publish crew event to RabbitMQ', { error: err.message, routingKey });
  }
}

// WebSocket broadcast
function broadcastCrewUpdate(update) {
  const msg = JSON.stringify(update);
  let sent = 0;
  wss.clients.forEach(client => {
    if (client.readyState === 1) { // WebSocket.OPEN
      client.send(msg);
      sent++;
    }
  });
  if (sent > 0) logger.debug('WebSocket broadcast', { type: update.type, clients: sent });
}

// ============================================================
// Request logging middleware
// ============================================================
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
    } else if (duration > 3000) {
      logger.warn('Slow crew dispatch request', meta);
    } else {
      logger.debug('Request completed', meta);
    }
  });
  next();
});

// ============================================================
// ETR Calculation
// ============================================================
function calculateETR(outage) {
  const baseMins = {
    'Transformer failure': 180,
    'Severe weather - ice storm': 360,
    'Vehicle accident - downed line': 120,
    'Underground cable fault': 480,
    'Equipment overload': 90,
    'Planned maintenance': 240,
    'Tree contact with power line': 60,
    'Substation relay trip': 45,
    'Lightning strike': 150,
    'Aging infrastructure failure': 300,
    'Animal contact': 30,
    'Construction damage': 210
  };
  const base = baseMins[outage.cause] || 120;
  // Add randomness +/- 25%
  const variance = base * (0.75 + Math.random() * 0.5);
  // Scale by affected customers (larger outages take longer)
  const scale = outage.affectedCustomers > 2000 ? 1.5 : outage.affectedCustomers > 500 ? 1.2 : 1.0;
  const totalMins = Math.round(variance * scale);
  return new Date(Date.now() + totalMins * 60000).toISOString();
}

// ============================================================
// Dispatch Logic
// ============================================================
function findBestCrew(outage) {
  // Find available crew, prefer matching region and skills
  const available = crews.filter(c => c.status === 'Available');
  if (available.length === 0) return null;

  // Score each crew
  const scored = available.map(c => {
    let score = 0;
    // Region match bonus
    if (outage.location && c.region.toLowerCase().includes(outage.location.split(',')[0].toLowerCase().trim())) score += 10;
    // Skill match
    if (outage.equipmentType === 'Substation' && c.skills.includes('substation')) score += 5;
    if (outage.equipmentType === 'Transformer' && c.skills.includes('transformer')) score += 5;
    if (outage.cause && outage.cause.includes('Underground') && c.skills.includes('underground')) score += 5;
    if (outage.priority === 'Critical' && c.skills.includes('emergency')) score += 8;
    // Larger crew for bigger outages
    if (outage.affectedCustomers > 1000 && c.members >= 4) score += 3;
    return { crew: c, score };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0].crew;
}

async function dispatchCrew(outage) {
  const crew = findBestCrew(outage);
  if (!crew) {
    logger.warn('No crews available for dispatch', { outageId: outage.id, priority: outage.priority });
    return null;
  }

  dispatchCounter++;
  const dispatch = {
    dispatchId: `DSP-${String(dispatchCounter).padStart(4, '0')}`,
    outageId: outage.id,
    crewId: crew.id,
    crewName: crew.name,
    crewLead: crew.lead,
    crewMembers: crew.members,
    vehicle: crew.vehicle,
    status: 'Dispatched',
    priority: outage.priority,
    location: outage.location,
    cause: outage.cause,
    affectedCustomers: outage.affectedCustomers,
    etr: calculateETR(outage),
    dispatchedAt: new Date().toISOString(),
    arrivedAt: null,
    completedAt: null,
    travelTimeMinutes: 15 + Math.floor(Math.random() * 45),
    notes: []
  };

  crew.status = 'Dispatched';
  crew.currentAssignment = dispatch.dispatchId;
  dispatchHistory.push(dispatch);

  // Persist to DB
  try {
    await pool.query(`
      INSERT INTO outages.crew_dispatches (dispatch_id, outage_id, crew_id, crew_name, crew_lead, status, priority, location, cause, affected_customers, etr, dispatched_at, travel_time_minutes)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
      ON CONFLICT (dispatch_id) DO NOTHING
    `, [dispatch.dispatchId, dispatch.outageId, dispatch.crewId, dispatch.crewName, dispatch.crewLead, dispatch.status, dispatch.priority, dispatch.location, dispatch.cause, dispatch.affectedCustomers, dispatch.etr, dispatch.dispatchedAt, dispatch.travelTimeMinutes]);
    logger.debug('Dispatch persisted to database', { dispatchId: dispatch.dispatchId });
  } catch (err) {
    logger.error('Failed to persist dispatch to database', { error: err.message, dispatchId: dispatch.dispatchId });
  }

  // Publish to RabbitMQ
  publishCrewEvent('crew.dispatched', dispatch);

  // Notify notification service
  try {
    await axios.post(`${NOTIFICATION_URL}/api/notifications/dispatch`, {
      dispatchId: dispatch.dispatchId,
      outageId: outage.id,
      crewName: crew.name,
      etr: dispatch.etr,
      location: outage.location,
      affectedCustomers: outage.affectedCustomers,
      priority: outage.priority
    }, { timeout: 3000 });
    logger.debug('Notification service notified of dispatch', { dispatchId: dispatch.dispatchId });
  } catch (err) {
    logger.warn('Failed to notify notification service', { error: err.message });
  }

  // WebSocket broadcast
  broadcastCrewUpdate({ type: 'crew-dispatched', dispatch });

  logger.info('Crew dispatched', {
    dispatchId: dispatch.dispatchId, crewId: crew.id, crewName: crew.name,
    outageId: outage.id, priority: outage.priority, etr: dispatch.etr
  });

  return dispatch;
}

// ============================================================
// Background: Simulate crew progress (arrive → working → complete)
// ============================================================
setInterval(() => {
  const active = dispatchHistory.filter(d => d.status !== 'Completed' && d.status !== 'Cancelled');
  active.forEach(dispatch => {
    const elapsed = (Date.now() - new Date(dispatch.dispatchedAt).getTime()) / 60000;

    if (dispatch.status === 'Dispatched' && elapsed >= dispatch.travelTimeMinutes) {
      // Crew arrives on-site
      dispatch.status = 'On-Site';
      dispatch.arrivedAt = new Date().toISOString();
      const crew = crews.find(c => c.id === dispatch.crewId);
      if (crew) crew.status = 'On-Site';

      publishCrewEvent('crew.status.arrived', dispatch);
      broadcastCrewUpdate({ type: 'crew-arrived', dispatch });
      logger.info('Crew arrived on-site', { dispatchId: dispatch.dispatchId, crewId: dispatch.crewId, outageId: dispatch.outageId });

      // Notify of arrival
      axios.post(`${NOTIFICATION_URL}/api/notifications/crew-arrived`, {
        dispatchId: dispatch.dispatchId,
        outageId: dispatch.outageId,
        crewName: dispatch.crewName,
        etr: dispatch.etr,
        location: dispatch.location
      }, { timeout: 3000 }).catch(() => {});
    }

    if (dispatch.status === 'On-Site') {
      const workTime = elapsed - dispatch.travelTimeMinutes;
      const etrMinutes = (new Date(dispatch.etr).getTime() - new Date(dispatch.dispatchedAt).getTime()) / 60000;
      const expectedWorkTime = etrMinutes - dispatch.travelTimeMinutes;

      if (workTime >= expectedWorkTime * (0.8 + Math.random() * 0.4)) {
        // Work complete — restore power
        dispatch.status = 'Completed';
        dispatch.completedAt = new Date().toISOString();
        const crew = crews.find(c => c.id === dispatch.crewId);
        if (crew) {
          crew.status = 'Available';
          crew.currentAssignment = null;
        }

        // Persist completion
        pool.query(`UPDATE outages.crew_dispatches SET status='Completed', completed_at=$1 WHERE dispatch_id=$2`,
          [dispatch.completedAt, dispatch.dispatchId]).catch(() => {});

        publishCrewEvent('crew.status.completed', dispatch);
        broadcastCrewUpdate({ type: 'crew-completed', dispatch });
        logger.info('Crew completed restoration', {
          dispatchId: dispatch.dispatchId, crewId: dispatch.crewId,
          totalMinutes: Math.round((new Date(dispatch.completedAt) - new Date(dispatch.dispatchedAt)) / 60000)
        });

        // Notify of restoration
        axios.post(`${NOTIFICATION_URL}/api/notifications/restored`, {
          dispatchId: dispatch.dispatchId,
          outageId: dispatch.outageId,
          crewName: dispatch.crewName,
          location: dispatch.location,
          restoredAt: dispatch.completedAt
        }, { timeout: 3000 }).catch(() => {});
      }
    }
  });

  // ETR updates — periodically refine estimates
  const onSite = dispatchHistory.filter(d => d.status === 'On-Site');
  onSite.forEach(dispatch => {
    if (Math.random() < 0.15) {
      // Adjust ETR by +/- 15 minutes
      const adjustment = (Math.random() > 0.5 ? 1 : -1) * Math.floor(Math.random() * 15) * 60000;
      dispatch.etr = new Date(new Date(dispatch.etr).getTime() + adjustment).toISOString();

      publishCrewEvent('crew.status.etr-update', dispatch);
      broadcastCrewUpdate({ type: 'etr-updated', dispatch });
      logger.debug('ETR updated', { dispatchId: dispatch.dispatchId, newEtr: dispatch.etr });
    }
  });
}, 30000); // Every 30 seconds

// ============================================================
// HTTP-triggered simulation (for gateway orchestration)
// ============================================================
app.post('/api/crew/simulate', async (req, res) => {
  logger.info('POST /api/crew/simulate - triggering crew dispatch cycle');

  // ~5% chance: RabbitMQ connection failure
  if (Math.random() < 0.05) {
    logger.error('RabbitMQ connection lost during dispatch cycle', {
      error: 'Error: Connection closed: 320 (CONNECTION-FORCED) with message "CONNECTION_FORCED - broker forced connection closure with reason \'shutdown\'"',
      broker: 'rabbitmq:5672'
    });
  }

  // ~4% chance: Database pool timeout
  if (Math.random() < 0.04) {
    logger.error('Database connection pool timeout in crew dispatch', {
      error: 'TimeoutError: ResourceRequest timed out after 30000ms',
      pool: { total: 10, idle: 0, waiting: 5 }
    });
    return res.status(503).json({ error: 'Database connection pool exhausted' });
  }

  const results = { dispatched: 0, arrived: 0, completed: 0, etrUpdates: 0 };

  // Fetch active outages and dispatch crews to unassigned ones
  try {
    const { data: activeOutages } = await axios.get(`${OUTAGE_URL}/api/outages/active`, { timeout: 5000 });
    logger.debug('Fetched active outages', { count: (activeOutages || []).length });

    for (const outage of (activeOutages || []).slice(0, 5)) {
      const alreadyDispatched = dispatchHistory.find(d => d.outageId === outage.id && d.status !== 'Completed' && d.status !== 'Cancelled');
      if (!alreadyDispatched && crews.some(c => c.status === 'Available')) {
        // ~7% chance: dispatch routing failure
        if (Math.random() < 0.07) {
          logger.error('Crew dispatch routing algorithm failure', {
            error: 'TypeError: Cannot read properties of undefined (reading \'region\')',
            outageId: outage.id,
            stack: 'at findBestCrew (index.js:145:42)\n    at dispatchCrew (index.js:171:20)'
          });
          continue;
        }

        const dispatch = await dispatchCrew(outage);
        if (dispatch) results.dispatched++;
      }
    }
  } catch (err) {
    logger.warn('Failed to fetch active outages for dispatch', { error: err.message });
  }

  // Count status transitions from background loop
  results.activeDispatches = dispatchHistory.filter(d => d.status === 'Dispatched').length;
  results.onSiteCrews = dispatchHistory.filter(d => d.status === 'On-Site').length;
  results.availableCrews = crews.filter(c => c.status === 'Available').length;
  results.totalDispatches = dispatchHistory.length;

  logger.info('Crew dispatch cycle complete', results);
  res.json({ status: 'Crew dispatch cycle complete', ...results });
});

// ============================================================
// API Endpoints
// ============================================================
app.get('/api/crew/crews', (req, res) => {
  logger.info('GET /api/crew/crews', { count: crews.length });
  res.json(crews);
});

app.get('/api/crew/crews/available', (req, res) => {
  const available = crews.filter(c => c.status === 'Available');
  logger.info('GET /api/crew/crews/available', { count: available.length });
  res.json(available);
});

app.get('/api/crew/dispatches', (req, res) => {
  const limit = Math.min(parseInt(req.query.limit || '50'), 200);

  // ~3% chance: slow query
  if (Math.random() < 0.03) {
    const delay = 3000 + Math.floor(Math.random() * 4000);
    logger.warn('Slow dispatch history query', { delayMs: delay, totalDispatches: dispatchHistory.length });
    return setTimeout(() => res.json(dispatchHistory.slice(-limit).reverse()), delay);
  }

  logger.info('GET /api/crew/dispatches', { total: dispatchHistory.length, limit });
  res.json(dispatchHistory.slice(-limit).reverse());
});

app.get('/api/crew/dispatches/active', (req, res) => {
  const active = dispatchHistory.filter(d => d.status !== 'Completed' && d.status !== 'Cancelled');
  logger.info('GET /api/crew/dispatches/active', { count: active.length });
  logger.debug('Active dispatches breakdown', {
    dispatched: active.filter(d => d.status === 'Dispatched').length,
    onSite: active.filter(d => d.status === 'On-Site').length
  });
  res.json(active);
});

app.get('/api/crew/dispatches/:id', (req, res) => {
  const d = dispatchHistory.find(d => d.dispatchId === req.params.id);
  if (!d) return res.status(404).json({ error: 'Dispatch not found' });
  res.json(d);
});

app.get('/api/crew/stats', (req, res) => {
  const active = dispatchHistory.filter(d => d.status !== 'Completed' && d.status !== 'Cancelled');
  const completed = dispatchHistory.filter(d => d.status === 'Completed');
  const avgResponseTime = completed.length > 0
    ? Math.round(completed.reduce((sum, d) => sum + d.travelTimeMinutes, 0) / completed.length)
    : 0;
  const avgRestorationTime = completed.length > 0
    ? Math.round(completed.reduce((sum, d) => sum + (new Date(d.completedAt) - new Date(d.dispatchedAt)) / 60000, 0) / completed.length)
    : 0;

  res.json({
    totalCrews: crews.length,
    availableCrews: crews.filter(c => c.status === 'Available').length,
    dispatchedCrews: crews.filter(c => c.status === 'Dispatched').length,
    onSiteCrews: crews.filter(c => c.status === 'On-Site').length,
    totalDispatches: dispatchHistory.length,
    activeDispatches: active.length,
    completedDispatches: completed.length,
    avgResponseTimeMinutes: avgResponseTime,
    avgRestorationTimeMinutes: avgRestorationTime,
    byPriority: {
      Critical: dispatchHistory.filter(d => d.priority === 'Critical').length,
      High: dispatchHistory.filter(d => d.priority === 'High').length,
      Medium: dispatchHistory.filter(d => d.priority === 'Medium').length,
      Low: dispatchHistory.filter(d => d.priority === 'Low').length
    }
  });
});

app.get('/api/crew/health', (req, res) => {
  res.json({
    status: 'Healthy',
    service: 'CrewDispatchService',
    crewCount: crews.length,
    availableCrews: crews.filter(c => c.status === 'Available').length,
    activeDispatches: dispatchHistory.filter(d => d.status !== 'Completed' && d.status !== 'Cancelled').length,
    rabbitMQ: rabbitChannel ? 'Connected' : 'Disconnected',
    wsClients: wss.clients.size
  });
});

// WebSocket connection handling
wss.on('connection', (ws, req) => {
  logger.info('WebSocket client connected', { ip: req.socket.remoteAddress, totalClients: wss.clients.size });

  ws.on('close', () => {
    logger.debug('WebSocket client disconnected', { totalClients: wss.clients.size });
  });

  // Send current state on connect
  ws.send(JSON.stringify({
    type: 'initial-state',
    crews: crews,
    activeDispatches: dispatchHistory.filter(d => d.status !== 'Completed' && d.status !== 'Cancelled')
  }));
});

// ============================================================
// Startup
// ============================================================
(async () => {
  await connectRabbitMQ();

  // Create crew_dispatches table if not exists
  try {
    const client = await pool.connect();
    await client.query(`
      CREATE TABLE IF NOT EXISTS outages.crew_dispatches (
        dispatch_id VARCHAR(20) PRIMARY KEY,
        outage_id VARCHAR(20),
        crew_id VARCHAR(20),
        crew_name VARCHAR(100),
        crew_lead VARCHAR(100),
        status VARCHAR(20) DEFAULT 'Dispatched',
        priority VARCHAR(20),
        location VARCHAR(200),
        cause VARCHAR(200),
        affected_customers INTEGER,
        etr TIMESTAMPTZ,
        dispatched_at TIMESTAMPTZ DEFAULT NOW(),
        arrived_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        travel_time_minutes INTEGER
      )
    `);
    client.release();
    logger.info('Database table crew_dispatches ready');
  } catch (err) {
    logger.warn('Database table creation failed', { error: err.message });
  }
})();

const port = process.env.PORT || 3001;
server.listen(port, () => {
  logger.info(`Crew Dispatch Service running on port ${port} (HTTP + WebSocket)`);
});
