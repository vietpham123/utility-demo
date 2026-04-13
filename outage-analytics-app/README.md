# GenericUtility Outage Analytics Platform

A polyglot microservices platform simulating a utility company's grid operations center. It models outage management, SCADA telemetry, demand forecasting, crew dispatch, weather correlation, and more — generating rich, realistic observability data across distributed traces, real user monitoring (RUM), business events, and log analytics.

Designed for Kubernetes deployment with full-stack Dynatrace observability built in.

---

## Table of Contents

- [Purpose](#purpose)
- [Architecture](#architecture)
- [Services](#services-16-microservices--10-languages)
- [Infrastructure](#infrastructure)
- [UI Dashboard](#ui-dashboard)
- [Traffic Generators](#traffic-generators)
- [Dynatrace Integration](#dynatrace-integration)
- [Project Structure](#project-structure)
- [Deployment Guide](#deployment-guide)
- [Configuration Reference](#configuration-reference)
- [Demo Users](#demo-users)
- [Feature Flags & Fault Injection](#feature-flags--fault-injection)

---

## Purpose

This application simulates the operational technology (OT) and information technology (IT) systems of a large electric utility company. It is a **demonstration and observability showcase platform** designed to produce:

- **Distributed traces** spanning 4-5 service layers across 10 programming languages
- **Real User Monitoring (RUM)** sessions with custom user actions, session properties, and error reporting
- **Business events** ingested into Dynatrace for workflow analytics
- **Infrastructure metrics** from databases, message brokers, and caches
- **Log data** from polyglot services running on the JVM, CLR, Go runtime, BEAM VM, Python, Ruby, Rust, and Node.js

The platform models key utility workflows:
- Storm response and outage triage
- SCADA telemetry monitoring and alert correlation
- Crew dispatch and work order management
- Customer communication and notification delivery
- Demand forecasting and pricing analysis
- Reliability index tracking (IEEE 1366 — SAIDI, SAIFI, CAIDI)

---

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
                │   Business Events, Faults    │
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
   │  TimescaleDB (PostgreSQL 15)  │  Redis 7  │  Kafka  │
   │              RabbitMQ (AMQP)                          │
   └──────────────────────────────────────────────────────┘

   ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐
   │  Analytics UI │  │ Load Generator │  │ Browser Traffic Gen │
   │  (HTML/JS)    │  │  (Locust)      │  │  (Playwright)       │
   └──────────────┘  └────────────────┘  └────────────────────┘
```

### Inter-Service Call Chains (PurePath Depth)

The services are wired to produce deep distributed traces:

| Chain | Depth | Path |
|---|---|---|
| Aggregator deep fetch | 5 | Gateway → Aggregator → Outage → (data) |
| Notification delivery | 4 | Gateway → Notification → Customer → Audit |
| Reliability analysis | 4 | Gateway → Reliability → Outage + SCADA |
| Storm correlation | 4 | Gateway → Weather → SCADA → (data) |
| Grid topology | 4 | Gateway → Grid Topology → SCADA |
| Demand forecasting | 4 | Gateway → Forecast → Weather + Usage |
| Meter anomaly | 4 | Gateway → Meter Data → Grid Topology |

---

## Services (16 Microservices / 10 Languages)

| Service | Language | Port | Purpose |
|---|---|---|---|
| **outage-service** | Node.js 18 | 3000 | Outage CRUD, active tracking, statistics |
| **usage-service** | Node.js 18 | 3000 | Energy usage ingestion and queries |
| **scada-service** | C# / .NET 6 | 80 | SCADA telemetry: voltage, current, frequency, power factor |
| **meter-data-service** | Java 17 (Spring Boot) | 8080 | AMI/MDMS smart meter readings and anomaly detection |
| **grid-topology-service** | Node.js 18 | 3000 | Substations, feeders, transformers, DMS/GIS data |
| **reliability-service** | Python (Gunicorn) | 5000 | IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI) |
| **demand-forecast-service** | Node.js 18 | 3000 | Load forecasting, peak demand prediction |
| **crew-dispatch-service** | Node.js 18 | 3001 | Crew management, dispatching, WebSocket updates |
| **notification-service** | Python (Flask/Gunicorn) | 5001 | Multi-channel delivery: SMS, email, push, IVR |
| **weather-service** | Go 1.22 (+ gRPC) | 8080 / 50051 | NWS correlation, storm-mode alerts |
| **customer-service** | Ruby (Sinatra) | 4567 | User authentication, customer profiles, search |
| **aggregator-service** | Node.js 18 | 3002 | Cross-service dashboard data aggregation (5-phase deep chain) |
| **audit-service** | Kotlin (Ktor/Gradle) | 8090 | Audit trail logging |
| **pricing-service** | PHP 8.2 | 8000 | Rate calculations, tariff pricing |
| **work-order-service** | Elixir 1.16 (Phoenix) | 4000 | Work order lifecycle management (OTP) |
| **alert-correlation-service** | Rust (Actix-web) | 8070 | Multi-signal alert correlation (SCADA + weather + outage) |

**Supporting components:**

| Component | Language | Port | Purpose |
|---|---|---|---|
| **analytics-gateway** | Node.js (Express) | 3000 | API gateway, routing, WebSocket proxy, Business Events |
| **analytics-ui** | HTML/CSS/JS (Nginx) | 80 | Single-page analytics dashboard |
| **reverse-proxy** | Nginx | 80 | L7 routing, TLS termination, security headers |
| **load-generator** | Python (Locust) | 8089 | HTTP traffic simulator (API-level) |
| **browser-traffic-gen** | Node.js (Playwright) | — | Headless Chromium RUM session generator |

---

## Infrastructure

| Component | Version | Purpose | Default Config |
|---|---|---|---|
| **TimescaleDB** | PostgreSQL 15 | Time-series database for all service data | Port 5432, DB: `utilitydb`, User: `utilityuser` |
| **Redis** | 7 | Caching and session state | Port 6379, 128MB max, LRU eviction |
| **Kafka** | KRaft mode | Event streaming between services | Port 9092, 3 partitions, 24h retention |
| **RabbitMQ** | Latest | Task queues for notifications and crew dispatch | Port 5672 (AMQP) |

### Database Schemas

TimescaleDB contains these schemas with hypertables for time-series data:

- **`grid`** — substations, feeders, transformers, service points
- **`outages`** — outage records and status tracking
- **`reliability`** — IEEE 1366 reliability indices
- **`timeseries`** — SCADA readings, alerts, meter readings, anomalies, demand forecasts
- **`weather`** — weather observations, storm correlations

---

## UI Dashboard

The single-page application provides 18 navigable sections:

| Section | Description |
|---|---|
| **Overview** | KPI cards, outage map, real-time summary |
| **SCADA Telemetry** | Voltage, current, frequency readings from substations |
| **Outage Management** | Active/historical outages, ETR tracking, filters |
| **Meter Data (MDMS)** | Smart meter readings, anomaly detection |
| **Grid Topology** | Interactive map of substations, feeders, transformers |
| **Reliability Indices** | SAIDI, SAIFI, CAIDI trend charts |
| **Demand Forecast** | Load prediction and peak demand analysis |
| **Crew Dispatch** | Crew assignment, real-time status via WebSocket |
| **Notifications** | Customer notification history and delivery status |
| **Weather** | Current conditions, storm alerts, correlation data |
| **Customers** | Customer search, profiles, service history |
| **Pricing** | Rate calculator, tariff lookup |
| **Work Orders** | Work order lifecycle management |
| **Audit Log** | Cross-service audit trail |
| **Alert Correlation** | Multi-signal alert grouping and analysis |
| **Live Feed** | Real-time WebSocket event stream |
| **Service Health** | Health status of all microservices |
| **Feature Flags** | Fault injection toggles for demo scenarios |

---

## Traffic Generators

The platform includes three distinct traffic generation approaches:

### 1. Load Generator (Locust) — API-Level Traffic

HTTP-only traffic simulator that exercises all API endpoints. Does **not** generate RUM data.

```bash
# Port-forward to Locust UI
kubectl port-forward deployment/load-generator 8089:8089 -n <your-namespace>
# Open http://localhost:8089
```

**Features:**
- Simulates 15 personas with role-based navigation patterns
- Browser User-Agent spoofing (Chrome, Firefox, Safari, Edge, mobile)
- Geo-location simulation via `X-Forwarded-For` headers (10 US cities)
- Session persistence with unique `X-Session-Id`
- Target: `http://reverse-proxy` (internal cluster traffic)

**Key env vars:** `LOCUST_HOST`, `DEMO_PASSWORD`, `LOCUST_USERS`, `LOCUST_SPAWN_RATE`

### 2. Browser Traffic Generator (Playwright) — RUM Sessions

Headless Chromium sessions that execute the Dynatrace RUM JS agent, producing **real user sessions** visible in Dynatrace.

```bash
# Deploy
kubectl apply -f browser-traffic-generator/k8s-utility.yaml

# Scale up/down
kubectl scale deployment/browser-traffic-gen -n <your-namespace> --replicas=3  # enable
kubectl scale deployment/browser-traffic-gen -n <your-namespace> --replicas=0  # disable
```

**Features:**
- 15 weighted personas with role-based journey selection
- 16 predefined journeys (storm_response, outage_triage, executive_overview, etc.)
- Rich session properties sent to Dynatrace: role, region, department, shift type, journey count
- Custom user actions per journey and per step (navigate, search, drill-down, map interaction)
- ~5% simulated error reporting for realistic RUM error data
- Session outcome classification: productive / moderate / brief
- Configurable concurrent users, session duration, and interval

**Key env vars:** `APP_URL`, `APP_MODE`, `CONCURRENT_USERS`, `SESSION_INTERVAL`, `MAX_SESSION_MINUTES`, `DEMO_PASSWORD`

### 3. Traffic Controller — Orchestrated Simulation

Kubernetes-native controller that manages simulation waves (outage creation, crew dispatch, resolution cycles).

```bash
kubectl apply -f traffic-controller/k8s.yaml
```

---

## Dynatrace Integration

### Real User Monitoring (RUM)

The UI includes a Dynatrace RUM JS agent snippet in `index.html`. You must replace this with your own tenant's RUM snippet, which you can obtain from:

**Dynatrace UI → Applications & Microservices → Frontend → Setup → Manual injection**

The UI code (`extensions.js`) sends rich RUM data:
- **Custom user actions:** Navigation, login, search, CSV export, rate calculation, work order creation
- **Session properties (strings):** `user_role`, `user_region`, `user_name`, `login_method`, `app_version`, `current_section`, `session_outcome`
- **Session properties (integers):** `sections_visited`, `total_actions`, `search_count`, `export_count`, `api_error_count`, `session_duration_min`
- **Session properties (doubles):** `calculated_kwh`, `calculated_cost`, `actions_per_minute`
- **Error reporting:** API failures, login errors reported to RUM

### Business Events

The API gateway can send business events to Dynatrace for workflow analytics. Configure via environment variables:

| Variable | Purpose |
|---|---|
| `DT_TENANT_URL` | Your Dynatrace tenant URL (e.g., `https://<tenant-id>.apps.dynatrace.com`) |
| `DT_BIZEVENT_TOKEN` | API token with `bizevents.ingest` scope |

### OneAgent / Operator

Deploy the Dynatrace Operator to your Kubernetes cluster for automatic instrumentation of all services. The operator injects OneAgent into pods for distributed tracing, code-level visibility, and infrastructure monitoring.

---

## Project Structure

```
outage-analytics-app/
├── gateway/                       # API Gateway (Node.js/Express)
│   ├── Dockerfile
│   └── index.js                   # Routes, Business Events, fault injection
├── ui-web/                        # Analytics Dashboard
│   ├── Dockerfile                 # Nginx-based static serving
│   ├── index.html                 # SPA with 18 sections, Leaflet maps
│   ├── extensions.js              # Login, routing, RUM instrumentation
│   ├── extensions.css             # Dark theme styling
│   └── nginx.conf                 # Proxy rules (/api → gateway)
├── reverse-proxy/                 # NGINX L7 Proxy
│   ├── Dockerfile
│   └── nginx.conf                 # Routing, WebSocket, security headers
├── services/
│   ├── outage-service/            # Node.js
│   ├── usage-service/             # Node.js
│   ├── scada-service/             # C# (.NET 6)
│   ├── meter-data-service/        # Java 17 (Spring Boot)
│   ├── grid-topology-service/     # Node.js
│   ├── reliability-service/       # Python (Flask/Gunicorn)
│   ├── demand-forecast-service/   # Node.js
│   ├── crew-dispatch-service/     # Node.js
│   ├── notification-service/      # Python (Flask/Celery)
│   ├── weather-service/           # Go 1.22 (gRPC + HTTP)
│   ├── customer-service/          # Ruby (Sinatra)
│   ├── aggregator-service/        # Node.js
│   ├── audit-service/             # Kotlin (Ktor)
│   ├── pricing-service/           # PHP 8.2
│   ├── work-order-service/        # Elixir (Phoenix)
│   └── alert-correlation-service/ # Rust (Actix-web)
├── load-generator/                # Locust traffic simulator
│   ├── Dockerfile
│   └── locustfile.py
├── k8s/
│   └── all-in-one.yaml            # Full Kubernetes deployment manifest
└── infrastructure/
    └── k8s/
        └── infrastructure.yaml    # TimescaleDB, Redis, Kafka, RabbitMQ
```

**Also in the repository root:**

```
browser-traffic-generator/         # Playwright RUM session generator
├── Dockerfile
├── generator.js                   # 15 personas, 16 journeys, RUM enrichment
├── k8s-utility.yaml               # K8s manifest for utility mode
├── k8s-retail.yaml                # K8s manifest for retail mode
├── k8s-generic.yaml               # K8s manifest for generic mode
└── package.json

traffic-controller/                # K8s-native simulation orchestrator
└── k8s.yaml
```

---

## Deployment Guide

### Prerequisites

- Kubernetes cluster (1.26+)
- Container registry (ACR, Docker Hub, GCR, ECR, etc.)
- `kubectl` configured with cluster access
- Docker for building images
- (Optional) Dynatrace Operator installed for auto-instrumentation

### Step 1 — Build and Push Images

```bash
# Set your container registry
export REGISTRY=<your-registry>

# Build all service images
for dir in outage-service usage-service scada-service meter-data-service \
           grid-topology-service reliability-service demand-forecast-service \
           crew-dispatch-service notification-service weather-service \
           customer-service aggregator-service audit-service pricing-service \
           work-order-service alert-correlation-service; do
  docker build -t $REGISTRY/$dir:latest services/$dir/
  docker push $REGISTRY/$dir:latest
done

# Build supporting components
docker build -t $REGISTRY/analytics-gateway:latest gateway/
docker build -t $REGISTRY/analytics-ui:latest ui-web/
docker build -t $REGISTRY/reverse-proxy:latest reverse-proxy/
docker build -t $REGISTRY/load-generator:latest load-generator/

for img in analytics-gateway analytics-ui reverse-proxy load-generator; do
  docker push $REGISTRY/$img:latest
done

# Build browser traffic generator (from repo root)
docker build -t $REGISTRY/browser-traffic-gen:latest ../browser-traffic-generator/
docker push $REGISTRY/browser-traffic-gen:latest
```

### Step 2 — Configure Kubernetes Manifests

Update `k8s/all-in-one.yaml`:

1. Replace all `image:` references with your registry (e.g., `<YOUR_REGISTRY>/outage-service:latest`)
2. Replace `<DB_PASSWORD>` placeholders with a strong database password
3. Replace `<RABBITMQ_PASSWORD>` with a RabbitMQ password
4. Replace `<REGISTRY_SECRET>` with your image pull secret name
5. Set `DEMO_PASSWORD` environment variable for demo user authentication
6. (Optional) Set `DT_TENANT_URL` and `DT_BIZEVENT_TOKEN` on the gateway for Business Events

### Step 3 — Deploy

```bash
# Create namespace
kubectl create namespace <your-namespace>

# Create image pull secret (if using a private registry)
kubectl create secret docker-registry <secret-name> \
  --docker-server=<your-registry> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n <your-namespace>

# Deploy infrastructure first
kubectl apply -f infrastructure/k8s/infrastructure.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=timescaledb -n <your-namespace> --timeout=120s

# Deploy all services
kubectl apply -f k8s/all-in-one.yaml

# Verify all pods are running
kubectl get pods -n <your-namespace>
```

### Step 4 — Expose the Application

**Option A — Ingress with TLS (recommended):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: utility-ingress
  namespace: <your-namespace>
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

**Option B — LoadBalancer (quick test):**

```bash
kubectl expose deployment reverse-proxy --type=LoadBalancer --port=80 -n <your-namespace>
```

### Step 5 — Configure RUM (Optional)

1. In your Dynatrace tenant, create a Web Application and obtain the RUM JS snippet
2. Replace the `<script>` tag in `ui-web/index.html` (line 7) with your tenant's snippet
3. Rebuild and redeploy the `analytics-ui` image

### Step 6 — Start Traffic Generation

See [Traffic Generators](#traffic-generators) above for deploying Locust, browser traffic generator, and traffic controller.

---

## Configuration Reference

### Environment Variables

All sensitive values are configured via environment variables — never hardcode credentials.

| Variable | Services | Default | Description |
|---|---|---|---|
| `DB_HOST` | Most services | `timescaledb` | PostgreSQL host |
| `DB_PORT` | Most services | `5432` | PostgreSQL port |
| `DB_NAME` | Most services | `utilitydb` | Database name |
| `DB_USER` | Most services | `utilityuser` | Database user |
| `DB_PASSWORD` | Most services | — | Database password (**required**) |
| `DATABASE_URL` | Node.js services | — | Full connection string (alternative to individual vars) |
| `REDIS_URL` | Node.js services | — | Redis connection string |
| `RABBITMQ_URL` | notification, weather, crew | — | RabbitMQ AMQP URL |
| `DEMO_PASSWORD` | customer-service, load-gen, traffic-gen | `changeme` | Shared demo user password |
| `DT_TENANT_URL` | gateway | — | Dynatrace tenant URL for Business Events |
| `DT_BIZEVENT_TOKEN` | gateway | — | Dynatrace API token (`bizevents.ingest` scope) |
| `APP_URL` | browser-traffic-gen | `https://localhost` | Target URL for browser traffic |
| `CONCURRENT_USERS` | browser-traffic-gen | `3` | Parallel browser sessions |
| `MAX_SESSION_MINUTES` | browser-traffic-gen | `10` | Max duration per RUM session |

---

## Demo Users

The platform ships with 15 demo users across 8 roles. All users share a password configured via the `DEMO_PASSWORD` environment variable.

| Username | Role | Region |
|---|---|---|
| `operator_jones` | Operator | Chicago-Metro |
| `engineer_chen` | Engineer | Philadelphia-Metro |
| `manager_smith` | Manager | Baltimore-Metro |
| `analyst_garcia` | Analyst | DC-Metro |
| `dispatcher_lee` | Dispatcher | Atlantic-Coast |
| `supervisor_patel` | Supervisor | Delaware-Valley |
| `technician_wong` | Technician | Chicago-Metro |
| `director_johnson` | Director | DC-Metro |
| `operator_brown` | Operator | Baltimore-Metro |
| `engineer_martinez` | Engineer | Philadelphia-Metro |
| `analyst_taylor` | Analyst | Atlantic-Coast |
| `dispatcher_harris` | Dispatcher | Chicago-Metro |
| `technician_clark` | Technician | DC-Metro |
| `manager_lewis` | Manager | Delaware-Valley |
| `operator_robinson` | Operator | Baltimore-Metro |

---

## Feature Flags & Fault Injection

The gateway includes a fault injection engine for demonstrating observability scenarios:

| Scenario | Endpoint | Effect |
|---|---|---|
| Database Outage | `POST /api/fault/inject` `{"scenario":"database-outage"}` | Simulates DB connection failures |
| Cascade Failure | `POST /api/fault/inject` `{"scenario":"cascade-failure"}` | Triggers cross-service error propagation |
| Resource Exhaustion | `POST /api/fault/inject` `{"scenario":"resource-exhaustion"}` | Simulates memory/CPU pressure |
| Network Partition | `POST /api/fault/inject` `{"scenario":"network-partition"}` | Drops inter-service communication |
| Clear All | `POST /api/fault/clear` | Restores normal operation |

These can also be toggled from the **Feature Flags** tab in the UI.

---

## Security Notes

- All passwords and tokens are configured via environment variables
- No credentials are hardcoded in the source code — default fallbacks use `changeme` placeholders
- K8s manifests use `<PLACEHOLDER>` tokens that must be replaced before deployment
- The Dynatrace RUM JS snippet in `index.html` is tenant-specific and must be replaced with your own
- Database passwords, registry secrets, and API tokens should be managed via Kubernetes Secrets
- The reverse proxy applies security headers: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`
