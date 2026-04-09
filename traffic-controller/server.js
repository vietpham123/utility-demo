const express = require('express');
const k8s = require('@kubernetes/client-node');
const path = require('path');
const http = require('http');

const app = express();
app.use(express.json());

// K8s client — auto-configures from in-cluster service account
const kc = new k8s.KubeConfig();
kc.loadFromDefault();

// Use raw kc.applyToRequest for direct REST calls — avoids client-node version issues
const cluster = kc.getCurrentCluster();
const API_BASE = cluster.server;

function k8sRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlPath, API_BASE);
    const opts = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method,
      headers: { 'Accept': 'application/json' },
    };
    if (body) {
      const json = JSON.stringify(body);
      opts.headers['Content-Type'] = method === 'PATCH'
        ? 'application/strategic-merge-patch+json' : 'application/json';
      opts.headers['Content-Length'] = Buffer.byteLength(json);
    }

    // Use https module if TLS
    const mod = url.protocol === 'https:' ? require('https') : http;
    const reqOpts = { ...opts, rejectUnauthorized: false };

    // Apply K8s auth (service account token)
    kc.applyToHTTPSOptions(reqOpts);

    const req = mod.request(reqOpts, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const parsed = res.headers['content-type']?.includes('json')
            ? JSON.parse(data) : data;
          if (res.statusCode >= 400) {
            reject({ status: res.statusCode, message: parsed.message || data });
          } else {
            resolve(parsed);
          }
        } catch {
          resolve(data);
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// Generators we manage
const GENERATORS = [
  {
    id: 'utility-browser',
    label: 'Utility — Browser (Playwright)',
    namespace: 'utility-outage-analytics',
    deployment: 'browser-traffic-gen',
    type: 'browser',
  },
  {
    id: 'retail-browser',
    label: 'Retail — Browser (Playwright)',
    namespace: 'retail',
    deployment: 'browser-traffic-gen',
    type: 'browser',
  },
  {
    id: 'utility-locust',
    label: 'Utility — Locust (HTTP)',
    namespace: 'utility-outage-analytics',
    deployment: 'load-generator',
    type: 'locust',
  },
  {
    id: 'retail-locust',
    label: 'Retail — Locust (HTTP)',
    namespace: 'retail',
    deployment: 'load-generator',
    type: 'locust',
  },
];

// Serve static UI
app.use(express.static(path.join(__dirname, 'public')));

// GET /api/generators — status of all generators
app.get('/api/generators', async (req, res) => {
  const results = [];
  for (const gen of GENERATORS) {
    try {
      const dep = await k8sRequest('GET',
        `/apis/apps/v1/namespaces/${gen.namespace}/deployments/${gen.deployment}`);
      const replicas = dep.spec.replicas || 0;
      const ready = dep.status.readyReplicas || 0;
      const container = dep.spec.template.spec.containers[0];
      const envVars = {};
      (container.env || []).forEach(e => { envVars[e.name] = e.value || ''; });

      results.push({
        ...gen,
        enabled: replicas > 0,
        replicas,
        ready,
        config: {
          CONCURRENT_USERS: envVars.CONCURRENT_USERS || '3',
          NAVIGATIONS_PER_SESSION: envVars.NAVIGATIONS_PER_SESSION || '10',
          SESSION_INTERVAL: envVars.SESSION_INTERVAL || '60',
          APP_URL: envVars.APP_URL || envVars.LOCUST_HOST || '',
        },
      });
    } catch (err) {
      results.push({
        ...gen,
        enabled: false,
        replicas: 0,
        ready: 0,
        config: {},
        error: err.message || String(err),
      });
    }
  }
  res.json(results);
});

// POST /api/generators/:id/toggle — enable/disable
app.post('/api/generators/:id/toggle', async (req, res) => {
  const gen = GENERATORS.find(g => g.id === req.params.id);
  if (!gen) return res.status(404).json({ error: 'Not found' });

  try {
    const dep = await k8sRequest('GET',
      `/apis/apps/v1/namespaces/${gen.namespace}/deployments/${gen.deployment}`);
    const current = dep.spec.replicas || 0;
    const target = current > 0 ? 0 : 1;
    await k8sRequest('PATCH',
      `/apis/apps/v1/namespaces/${gen.namespace}/deployments/${gen.deployment}`,
      { spec: { replicas: target } });
    res.json({ ok: true, replicas: target });
  } catch (err) {
    res.status(500).json({ error: err.message || String(err) });
  }
});

// POST /api/generators/:id/config — update env vars (browser generators)
app.post('/api/generators/:id/config', async (req, res) => {
  const gen = GENERATORS.find(g => g.id === req.params.id);
  if (!gen) return res.status(404).json({ error: 'Not found' });

  const { CONCURRENT_USERS, NAVIGATIONS_PER_SESSION, SESSION_INTERVAL } = req.body;

  try {
    const dep = await k8sRequest('GET',
      `/apis/apps/v1/namespaces/${gen.namespace}/deployments/${gen.deployment}`);
    const container = dep.spec.template.spec.containers[0];
    const envMap = {};
    (container.env || []).forEach(e => { envMap[e.name] = e.value; });

    if (CONCURRENT_USERS) envMap.CONCURRENT_USERS = String(CONCURRENT_USERS);
    if (NAVIGATIONS_PER_SESSION) envMap.NAVIGATIONS_PER_SESSION = String(NAVIGATIONS_PER_SESSION);
    if (SESSION_INTERVAL) envMap.SESSION_INTERVAL = String(SESSION_INTERVAL);

    container.env = Object.entries(envMap).map(([name, value]) => ({ name, value }));

    await k8sRequest('PUT',
      `/apis/apps/v1/namespaces/${gen.namespace}/deployments/${gen.deployment}`,
      dep);
    res.json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: err.message || String(err) });
  }
});

// GET /api/generators/:id/logs — recent logs
app.get('/api/generators/:id/logs', async (req, res) => {
  const gen = GENERATORS.find(g => g.id === req.params.id);
  if (!gen) return res.status(404).json({ error: 'Not found' });

  try {
    const pods = await k8sRequest('GET',
      `/api/v1/namespaces/${gen.namespace}/pods?labelSelector=app%3D${gen.deployment}`);
    if (!pods.items || !pods.items.length) return res.json({ logs: '(no pods running)' });

    const podName = pods.items[0].metadata.name;
    const containerName = gen.deployment === 'browser-traffic-gen'
      ? 'browser-traffic-gen' : 'load-generator';
    const logs = await k8sRequest('GET',
      `/api/v1/namespaces/${gen.namespace}/pods/${podName}/log?container=${containerName}&tailLines=80`);
    res.json({ logs: logs || '(empty)' });
  } catch (err) {
    res.json({ logs: `Error: ${err.message || String(err)}` });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`Traffic Controller UI on :${PORT}`));
