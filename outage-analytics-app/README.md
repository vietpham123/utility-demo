# GenericUtility Outage Analytics Platform

A polyglot microservices platform for utility grid operations — outage management, SCADA telemetry, demand forecasting, crew dispatch, and more. Designed for Kubernetes deployment with observability built in.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX Reverse Proxy                         │
│                     (L7 routing, TLS termination)                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │       API Gateway           │
                │       (Node.js/Express)      │
                │   Route aggregation, auth,   │
                │   WebSocket, search          │
                └──────────────┬──────────────┘
                               │
        ┌──────────┬───────────┼───────────┬──────────┐
        │          │           │           │          │
   ┌────┴────┐┌───┴────┐┌────┴─────┐┌───┴────┐┌───┴─────┐
   │ Outage  ││ SCADA  ││  Meter   ││ Grid   ││Reliab.  │
   │ Service ││Service ││  Data    ││Topology││ Service │
   │(Node.js)││(.NET 6)││(Java 17) ││(Node)  ││(Python) │
   └────┬────┘└───┬────┘└────┬─────┘└───┬────┘└───┬─────┘
        │         │          │          │         │
   ┌────┴────┐┌───┴────┐┌───┴─────┐┌──┴─────┐┌──┴──────┐
   │Forecast ││ Crew   ││Notific. ││Weather ││Customer │
   │ Service ││Dispatch││ Service ││Service ││ Service │
   │(Node.js)││(Node)  ││(Python) ││(Go)    ││ (Ruby)  │
   └─────────┘└────────┘└─────────┘└────────┘└─────────┘
        │          │          │          │         │
   ┌────┴────┐┌───┴────┐┌───┴─────┐┌──┴─────┐┌──┴──────┐
   │Aggregat.││ Audit  ││Pricing  ││Work    ││Alert    │
   │ Service ││Service ││ Service ││ Order  ││Correlat.│
   │(Node.js)││(Kotlin)││ (PHP)   ││(Elixir)││ (Rust)  │
   └─────────┘└────────┘└─────────┘└────────┘└─────────┘

   ┌──────────────────────────────────────────────────────┐
   │              Infrastructure Layer                     │
   │  TimescaleDB (PostgreSQL)  │  Redis  │  Kafka  │ RMQ │
   └──────────────────────────────────────────────────────┘

   ┌──────────────┐    ┌────────────────┐
   │  Analytics UI │    │ Load Generator │
   │  (HTML/JS)    │    │  (Locust/Python)│
   └──────────────┘    └────────────────┘
```

## Services (10 languages)

| Service | Language | Purpose |
|---|---|---|
| outage-service | Node.js | Outage CRUD, active tracking, stats |
| usage-service | Node.js | Energy usage ingestion and queries |
| scada-service | .NET 6 (C#) | SCADA telemetry readings and alerts |
| meter-data-service | Java 17 (Spring Boot) | Smart meter readings and anomalies |
| grid-topology-service | Node.js | Substations, feeders, transformers |
| reliability-service | Python | IEEE 1366 reliability indices (SAIDI/SAIFI) |
| demand-forecast-service | Node.js | Load forecasting and peak demand |
| crew-dispatch-service | Node.js | Crew management and dispatch |
| notification-service | Python | Customer notification delivery |
| weather-service | Go | Weather conditions, alerts, correlations |
| customer-service | Ruby (Sinatra) | Customer management, auth, user profiles |
| aggregator-service | Node.js | Cross-service data aggregation |
| audit-service | Kotlin (Ktor) | Audit trail logging |
| pricing-service | PHP | Rate calculations and pricing |
| work-order-service | Elixir (Phoenix) | Work order lifecycle management |
| alert-correlation-service | Rust (Actix) | Multi-signal alert correlation |
| analytics-gateway | Node.js | API gateway, routing, WebSocket |
| analytics-ui | HTML/JS | Single-page analytics dashboard |
| reverse-proxy | NGINX | L7 reverse proxy |
| load-generator | Python (Locust) | UI navigation traffic simulator |

## Infrastructure

- **TimescaleDB** — PostgreSQL with time-series extensions for all service data
- **Redis** — Caching and session state
- **Kafka** (KRaft mode) — Event streaming between services
- **RabbitMQ** — Task queues for notifications and crew dispatch

## UI Tabs

The dashboard has 18 navigable sections:

Overview · SCADA Telemetry · Outage Management · Meter Data (MDMS) · Grid Topology · Reliability Indices · Demand Forecast · Crew Dispatch · Notifications · Weather · Customers · Pricing · Work Orders · Audit Log · Alert Correlation · Live Feed · Service Health · Feature Flags

## Project Structure

```
outage-analytics-app/
├── services/
│   ├── outage-service/          # Node.js
│   ├── usage-service/           # Node.js
│   ├── scada-service/           # .NET 6
│   ├── meter-data-service/      # Java 17 / Spring Boot
│   ├── grid-topology-service/   # Node.js
│   ├── reliability-service/     # Python
│   ├── demand-forecast-service/ # Node.js
│   ├── crew-dispatch-service/   # Node.js
│   ├── notification-service/    # Python
│   ├── weather-service/         # Go
│   ├── customer-service/        # Ruby
│   ├── aggregator-service/      # Node.js
│   ├── audit-service/           # Kotlin
│   ├── pricing-service/         # PHP
│   ├── work-order-service/      # Elixir
│   └── alert-correlation-service/ # Rust
├── gateway/                     # API Gateway (Node.js)
├── ui-web/                      # Analytics Dashboard (HTML/JS)
├── reverse-proxy/               # NGINX config
├── load-generator/              # Locust traffic simulator
├── k8s/                         # Kubernetes manifests
│   └── all-in-one.yaml
└── infrastructure/
    └── k8s/                     # Infrastructure (DB, cache, queue)
```

## Deployment

### Prerequisites

- Kubernetes cluster (1.26+)
- Container registry (ACR, Docker Hub, etc.)
- `kubectl` configured
- Docker for building images

### 1. Build and Push Images

```bash
# Set your registry
export REGISTRY=<your-registry>

# Build all service images
for svc in outage-service usage-service scada-service meter-data-service \
           grid-topology-service reliability-service demand-forecast-service \
           crew-dispatch-service notification-service weather-service \
           customer-service aggregator-service audit-service pricing-service \
           work-order-service alert-correlation-service analytics-gateway \
           analytics-ui reverse-proxy load-generator; do
  docker build -t $REGISTRY/$svc:latest services/$svc/ 2>/dev/null || \
  docker build -t $REGISTRY/$svc:latest $svc/
  docker push $REGISTRY/$svc:latest
done
```

### 2. Configure Kubernetes Manifest

Update `k8s/all-in-one.yaml`:

- Replace all `image:` references with your registry
- Replace password placeholders (`<DB_PASSWORD>`) with your values
- Replace `<REGISTRY_SECRET>` with your image pull secret name
- Adjust resource limits as needed

### 3. Deploy

```bash
# Create namespace
kubectl create namespace <your-namespace>

# Create image pull secret (if using private registry)
kubectl create secret docker-registry <secret-name> \
  --docker-server=<your-registry> \
  --docker-username=<user> \
  --docker-password=<password> \
  -n <your-namespace>

# Deploy everything
kubectl apply -f k8s/all-in-one.yaml

# Verify all pods are running
kubectl get pods -n <your-namespace>
```

### 4. Expose the Application

Option A — **Ingress with TLS** (recommended):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: utility-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [<your-domain>]
      secretName: utility-tls
  rules:
    - host: <your-domain>
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: reverse-proxy
                port:
                  number: 80
```

Option B — **LoadBalancer Service** (quick test):
```bash
kubectl expose deployment reverse-proxy --type=LoadBalancer --port=80 -n <your-namespace>
```

### 5. Load Generator (Locust)

The Locust web UI is exposed on port 8089. Access it via Ingress or port-forward:

```bash
kubectl port-forward deployment/load-generator 8089:8089 -n <your-namespace>
# Open http://localhost:8089
```

Configure number of users, spawn rate, and start the test. Locust emulates real users navigating through all 18 UI tabs.

## Demo Users

The platform ships with 15 demo users across 7 roles (operator, engineer, manager, analyst, dispatcher, supervisor, technician, director). User credentials are configured in the customer-service.

## Feature Flags

The Feature Flags tab allows fault injection for demo/testing:
- Database outage simulation
- Network latency injection
- Service degradation scenarios

Use the UI toggles or the `/api/fault/inject` and `/api/fault/clear` endpoints.
