# Outage Analytics Platform

A polyglot microservices application for utility outage management, grid monitoring, and weather-driven analytics. Deployed on AKS with Dynatrace OneAgent for full-stack observability.

**Access:** http://20.165.22.240 (via reverse proxy)  
**Namespace:** `utility-outage-analytics`  
**Services:** 18 microservices + 4 infrastructure pods + reverse proxy + load generator = **24 pods**  
**Languages:** Node.js, .NET 6, Java 17, Python 3.11, Go 1.22, Ruby 3.2, Kotlin, PHP 8.2, Elixir 1.16, Rust 1.75

## Architecture (v2.0)

```
  ┌────────────────────┐     ┌─────────────────────┐
  │  Load Generator    │     │  Reverse Proxy       │ :80 (LoadBalancer)
  │  (Python/Locust)   │────▶│  (Nginx)             │
  └────────────────────┘     └──────┬────────┬──────┘
                                    │        │
                         ┌──────────▼──┐  ┌──▼───────────┐
                         │ Analytics UI│  │ Analytics    │
                         │ (Nginx SPA) │  │ Gateway      │
                         │ :80         │  │ (Node.js)    │
                         └─────────────┘  │ :3000 + WS   │
                                          └──┬──┬──┬──┬──┘
           ┌──────────────┬──────────────────┘  │  │  └──────────────┬──────────────┐
           │    ┌─────────┘            ┌────────┘  └──────┐          │              │
           ▼    ▼                      ▼                  ▼          ▼              ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │  ORIGINAL SERVICES (10)                                                              │
  │  Outage(Node) | Usage(Node) | SCADA(.NET) | Meter(Java) | Grid(Node) |              │
  │  Reliability(Python) | Forecast(Node) | Crew(Node) | Notification(Python) |          │
  │  Weather(Go/gRPC)                                                                    │
  └──────────────────────────────────────────────────────────────────────────────────────┘
           │              │              │               │             │
           ▼              ▼              ▼               ▼             ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │  PHASE 1-3 NEW SERVICES (8)                                                          │
  │  Aggregator(Node) | Customer(Ruby) | Audit(Kotlin) | Pricing(PHP) |                  │
  │  Work-Order(Elixir) | Alert-Correlation(Rust) | Reverse-Proxy(Nginx) |               │
  │  Load-Generator(Python/Locust)                                                       │
  └──────────────────────────────────────────────────────────────────────────────────────┘
           │         │         │        │     │          │         │          │
           ▼         ▼         ▼        ▼     ▼          ▼         ▼          ▼
  ┌──────────┐ ┌───────┐ ┌──────────────────┐ ┌───────────────────────────────┐
  │TimescaleDB│ │ Redis │ │     Kafka        │ │         RabbitMQ              │
  │(PG 15)   │ │  7    │ │  (KRaft mode)    │ │  3.13-management              │
  │ :5432    │ │ :6379 │ │  :9092           │ │  :5672 (AMQP) :15672 (Mgmt)  │
  └──────────┘ └───────┘ └──────────────────┘ └───────────────────────────────┘
```

## Services (18 Microservices + Infrastructure)

| Service | Language | Port | Description | Dependencies |
|---|---|---|---|---|
| **outage-service** | Node.js 18 | 3000 | Outage tracking, status management, crew assignment | TimescaleDB, Kafka, Redis, Grid Topology |
| **usage-service** | Node.js 18 | 3000 | Energy usage monitoring and analytics | Kafka, Redis |
| **scada-service** | .NET 6 | 80 | SCADA sensor telemetry simulation and alerts | TimescaleDB, Kafka, Redis |
| **meter-data-service** | Java 17 / Spring Boot 3.2 | 8080 | Smart meter data ingestion (MDMS), VEE validation | TimescaleDB, Kafka, Redis |
| **grid-topology-service** | Node.js 18 | 3000 | Electrical grid model (substations → feeders → transformers → service points) | TimescaleDB, Redis, Kafka |
| **reliability-service** | Python 3.11 / Flask | 5000 | IEEE 1366 reliability indices (SAIDI, SAIFI, CAIDI, MAIFI) | TimescaleDB, Kafka |
| **demand-forecast-service** | Node.js 18 | 3000 | Load forecasting by area with capacity planning | TimescaleDB, Redis, Kafka |
| **crew-dispatch-service** | Node.js 18 | 3001 | Crew management, dispatch, WebSocket live updates | TimescaleDB, RabbitMQ |
| **notification-service** | Python 3.11 / Flask | 5001 | Multi-channel alerts (SMS, email, push, IVR) via Celery | TimescaleDB, RabbitMQ |
| **weather-service** | Go 1.22 | 8080 + 50051 | NWS weather simulation, storm-outage correlation, gRPC | TimescaleDB, RabbitMQ |
| **aggregator-service** | Node.js 18 | 3002 | Deep multi-hop orchestration, dashboard aggregation, report generation | All services |
| **customer-service** | Ruby 3.2 / Sinatra | 4567 | User authentication, customer management, search, preferences | — |
| **audit-service** | Kotlin / Ktor | 8090 | Kafka event audit trail, searchable log, statistics | Kafka |
| **pricing-service** | PHP 8.2 | 8000 | Energy pricing, rate classes, time-of-use calculation, outage cost impact | — |
| **work-order-service** | Elixir 1.16 / Plug | 4000 | Work order CRUD, cross-service enrichment | Customer, Audit |
| **alert-correlation-service** | Rust 1.75 / Actix | 8070 | SCADA + weather + outage alert correlation engine | Weather, Outage |
| **reverse-proxy** | Nginx | 80 | Front-door proxy, RUM headers, WebSocket upgrade | Gateway, UI |
| **load-generator** | Python 3.11 / Locust | — | Continuous traffic generation (5 user personas) | Reverse Proxy |

## Gateway Simulation Orchestrator

The gateway runs a periodic simulation cycle (every 15s) that creates end-to-end Dynatrace PurePaths:

| Wave | Services | Purpose |
|---|---|---|
| **Wave 1** | SCADA, Weather | Sensor data generation (parallel) |
| **Wave 2** | Weather Correlation | Enrichment (sequential) |
| **Wave 3** | Outage, Usage, Forecast, Meter | Event processing (parallel) |
| **Wave 4** | Reliability | Analytics (sequential, depends on outage data) |
| **Wave 5** | Crew Dispatch → Notifications | Operations (sequential) |
| **Wave 6** | Pricing, Alert Correlation, Work Orders, Audit | Extended services (parallel) |

## Infrastructure

| Component | Image | Port | Purpose |
|---|---|---|---|
| TimescaleDB | `timescale/timescaledb:latest-pg15` | 5432 | Time-series database (DB: `utilitydb`) |
| Redis | `redis:7-alpine` | 6379 | Caching layer |
| Kafka | `vietregistry.azurecr.io/kafka:latest` | 9092 | Event streaming (KRaft, no ZooKeeper) |
| RabbitMQ | `rabbitmq:3.13-management-alpine` | 5672, 15672 | Message broker (crew dispatch, notifications, weather) |

## Sporadic Error Injection

Each service includes randomized failures for realistic Dynatrace error detection:

- **Gateway**: ~2% request slowdown (3-8s delay)
- **SCADA**: ~3% sensor read failures, ~2% calibration drift
- **Meter Data**: ~4% AMI network timeout, ~5% VEE validation failure
- **Outage**: ~3% GIS lookup failure, ~2% duplicate detection
- **Weather**: ~5% NWS API timeout, ~3% radar processing failure, ~6% correlation engine timeout
- **Crew Dispatch**: ~4% GPS timeout, ~3% radio communication failure
- **Notifications**: ~5% SMS gateway timeout, ~3% email bounce

## API Endpoints

All routes are accessible through the gateway at `/api/...`:

| Domain | Key Endpoints |
|---|---|
| **Outages** | `GET /api/outages`, `GET /api/outages/active`, `GET /api/outages/stats/summary` |
| **Usage** | `GET /api/usage`, `GET /api/usage/summary` |
| **SCADA** | `GET /api/scada/readings/latest`, `GET /api/scada/alerts`, `POST /api/scada/simulate` |
| **Metering** | `GET /api/meter-data/readings`, `GET /api/meter-data/anomalies` |
| **Grid** | `GET /api/grid/topology`, `GET /api/grid/substations` |
| **Reliability** | `GET /api/reliability/indices`, `GET /api/reliability/history` |
| **Forecast** | `GET /api/forecast/current`, `GET /api/forecast/peak-demand` |
| **Crew** | `GET /api/crew/crews`, `GET /api/crew/dispatches/active` |
| **Notifications** | `GET /api/notifications/stats`, `GET /api/notifications/log` |
| **Weather** | `GET /api/weather/conditions`, `GET /api/weather/forecast`, `GET /api/weather/alerts` |
| **Aggregator** | `GET /api/aggregate/dashboard`, `GET /api/aggregate/correlation`, `GET /api/aggregate/report/:type` |
| **Auth** | `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me` |
| **Customers** | `GET /api/customers`, `GET /api/customers/search?q=`, `GET /api/customers/stats` |
| **Pricing** | `GET /api/pricing/current`, `GET /api/pricing/calculate?rateClass=&region=&kwh=`, `GET /api/pricing/rates` |
| **Work Orders** | `GET /api/work-orders`, `POST /api/work-orders`, `PUT /api/work-orders/:id` |
| **Audit** | `GET /api/audit/log`, `GET /api/audit/stats`, `GET /api/audit/search?q=` |
| **Alerts** | `GET /api/alerts/correlated`, `GET /api/alerts/stats`, `POST /api/alerts/correlate` |
| **Search** | `GET /api/search?q=` (queries outages, customers, meters, crews, work orders, audit) |
| **System** | `POST /api/simulate/cycle`, `GET /api/dashboard`, `GET /api/health`, `WebSocket /ws` |

## Build and Deploy

```bash
ssh -i ~/.ssh/VPET_key.pem azureuser@52.248.43.42
cd ~/outage-analytics-app
ACR=vietregistry.azurecr.io

# Build all images
for svc in outage-service usage-service grid-topology-service demand-forecast-service crew-dispatch-service aggregator-service; do
  docker build -t $ACR/$svc:latest services/$svc/
done
docker build -t $ACR/scada-service:latest services/scada-service/                       # .NET
docker build -t $ACR/meter-data-service:latest services/meter-data-service/             # Java
docker build -t $ACR/reliability-service:latest services/reliability-service/            # Python
docker build -t $ACR/notification-service:latest services/notification-service/          # Python
docker build -t $ACR/weather-service:latest services/weather-service/                   # Go
docker build -t $ACR/customer-service:latest services/customer-service/                 # Ruby
docker build -t $ACR/audit-service:latest services/audit-service/                       # Kotlin
docker build -t $ACR/pricing-service:latest services/pricing-service/                   # PHP
docker build -t $ACR/work-order-service:latest services/work-order-service/             # Elixir
docker build -t $ACR/alert-correlation-service:latest services/alert-correlation-service/ # Rust
docker build -t $ACR/analytics-gateway:latest gateway/
docker build -t $ACR/analytics-ui:latest ui-web/
docker build -t $ACR/reverse-proxy:latest reverse-proxy/
docker build -t $ACR/load-generator:latest load-generator/

# Push and deploy
for img in outage-service usage-service scada-service meter-data-service grid-topology-service reliability-service demand-forecast-service crew-dispatch-service notification-service weather-service aggregator-service customer-service audit-service pricing-service work-order-service alert-correlation-service analytics-gateway analytics-ui reverse-proxy load-generator; do
  docker push $ACR/$img:latest
done

kubectl apply -f k8s/all-in-one.yaml
```

## Structure

```
├── gateway/              # Node.js API gateway + simulation orchestrator
│   ├── index.js
│   ├── logger.js
│   ├── package.json
│   └── Dockerfile
├── services/
│   ├── outage-service/        # Node.js
│   ├── usage-service/         # Node.js
│   ├── grid-topology-service/ # Node.js
│   ├── demand-forecast-service/ # Node.js
│   ├── crew-dispatch-service/ # Node.js + WebSocket + RabbitMQ
│   ├── scada-service/         # .NET 6 (C#)
│   ├── meter-data-service/    # Java 17 / Spring Boot 3.2
│   ├── reliability-service/   # Python 3.11 / Flask
│   ├── notification-service/  # Python 3.11 / Flask + Celery
│   └── weather-service/       # Go 1.22 + gRPC
│   ├── aggregator-service/    # Node.js — deep multi-hop orchestration
│   ├── customer-service/      # Ruby 3.2 / Sinatra — auth + customer mgmt
│   ├── audit-service/         # Kotlin / Ktor — Kafka audit trail
│   ├── pricing-service/       # PHP 8.2 — energy rate calculation
│   ├── work-order-service/    # Elixir 1.16 / Plug — work order CRUD
│   └── alert-correlation-service/ # Rust 1.75 / Actix — event correlation
├── ui-web/               # Nginx SPA (dark-themed analytics dashboard)
│   ├── index.html         # Main HTML shell
│   ├── extensions.css     # Phase 2-3 extended styles
│   └── extensions.js      # Login, search, WebSocket, pagination, export
├── reverse-proxy/        # Nginx front-door proxy (RUM headers, WebSocket)
├── load-generator/       # Python/Locust continuous traffic generation
├── k8s/
│   └── all-in-one.yaml   # Full deployment manifest (24 pods)
└── README.md

## Polyglot Coverage (10 Languages)

| Language | Services |
|---|---|
| Node.js 18 | Outage, Usage, Grid, Forecast, Crew, Gateway, Aggregator |
| .NET 6 (C#) | SCADA |
| Java 17 | Meter Data |
| Python 3.11 | Reliability, Notification, Load Generator |
| Go 1.22 | Weather (+ gRPC) |
| Ruby 3.2 | Customer |
| Kotlin | Audit |
| PHP 8.2 | Pricing |
| Elixir 1.16 | Work Order |
| Rust 1.75 | Alert Correlation |
```
