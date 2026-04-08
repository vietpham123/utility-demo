# Outage Analytics Platform

A polyglot microservices application for utility outage management, grid monitoring, and weather-driven analytics. Deployed on AKS with Dynatrace OneAgent for full-stack observability.

**Access:** http://20.165.22.240  
**Namespace:** `utility-outage-analytics`

## Architecture

```
                          ┌─────────────────────┐
                          │  Analytics UI        │ :80 (LoadBalancer)
                          │  (Nginx SPA)         │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │  Analytics Gateway    │ :3000
                          │  (Node.js/Express)    │
                          │  Simulation Orchestr. │
                          └──┬──┬──┬──┬──┬──┬──┬─┘
       ┌─────────────────────┘  │  │  │  │  │  └──────────────────────┐
       │        ┌───────────────┘  │  │  │  └────────────┐            │
       ▼        ▼                  ▼  ▼  ▼               ▼            ▼
  ┌─────────┬─────────┬──────────┬────┬────────┬───────────┬──────────┬──────────┐
  │ Outage  │ Usage   │ SCADA    │Grid│Meter   │Reliability│ Forecast │ Crew     │
  │ Service │ Service │ Service  │Topo│Data    │ Service   │ Service  │ Dispatch │
  │ Node.js │ Node.js │ .NET 6   │Node│Java 17 │ Python    │ Node.js  │ Node.js  │
  │ :3000   │ :3000   │ :80      │:3K │:8080   │ :5000     │ :3000    │ :3001    │
  └────┬────┴────┬────┴────┬─────┴──┬─┴───┬────┴─────┬────┴────┬─────┴────┬─────┘
       │         │         │        │     │          │         │          │
       ▼         ▼         ▼        ▼     ▼          ▼         ▼          ▼
  ┌──────────┐ ┌───────┐ ┌──────────────────┐ ┌───────────────────────────────┐
  │TimescaleDB│ │ Redis │ │     Kafka        │ │         RabbitMQ              │
  │(PG 15)   │ │  7    │ │  (KRaft mode)    │ │  3.13-management              │
  │ :5432    │ │ :6379 │ │  :9092           │ │  :5672 (AMQP) :15672 (Mgmt)  │
  └──────────┘ └───────┘ └──────────────────┘ └───────────────────────────────┘
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                        ┌───────────┐       ┌─────────────┐
                                        │Notification│      │ Weather     │
                                        │ Service    │      │ Service     │
                                        │ Python     │      │ Go 1.22     │
                                        │ :5001      │      │ :8080 + gRPC│
                                        └────────────┘      │ :50051      │
                                                            └─────────────┘
```

## Services (10 Microservices)

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
| **weather-service** | Go 1.22 | 8080 (HTTP) + 50051 (gRPC) | NWS weather simulation, storm-outage correlation, storm-mode alerts | TimescaleDB, RabbitMQ |

## Gateway Simulation Orchestrator

The gateway runs a periodic simulation cycle (every 15s) that creates end-to-end Dynatrace PurePaths:

| Wave | Services | Purpose |
|---|---|---|
| **Wave 1** | SCADA, Meter Data, Forecast, Weather | Data generators (parallel) |
| **Wave 2** | Outage, Usage | Event processors (parallel) |
| **Wave 3** | Reliability | Analytics (sequential, depends on outage data) |
| **Wave 4** | Crew Dispatch, Notifications | Operations (parallel, depends on outage data) |

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
| **System** | `POST /api/simulate/cycle`, `GET /api/dashboard`, `GET /api/health` |

## Build and Deploy

```bash
ssh -i ~/.ssh/VPET_key.pem azureuser@52.248.43.42
cd ~/outage-analytics-app
ACR=vietregistry.azurecr.io

# Build all images
for svc in outage-service usage-service grid-topology-service demand-forecast-service crew-dispatch-service; do
  docker build -t $ACR/$svc:latest services/$svc/
done
docker build -t $ACR/scada-service:latest services/scada-service/           # .NET
docker build -t $ACR/meter-data-service:latest services/meter-data-service/ # Java
docker build -t $ACR/reliability-service:latest services/reliability-service/ # Python
docker build -t $ACR/notification-service:latest services/notification-service/ # Python
docker build -t $ACR/weather-service:latest services/weather-service/       # Go
docker build -t $ACR/analytics-gateway:latest gateway/
docker build -t $ACR/analytics-ui:latest ui-web/

# Push and deploy
for img in outage-service usage-service scada-service meter-data-service grid-topology-service reliability-service demand-forecast-service crew-dispatch-service notification-service weather-service analytics-gateway analytics-ui; do
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
├── ui-web/               # Nginx SPA (dark-themed analytics dashboard)
├── k8s/
│   └── all-in-one.yaml   # Full deployment manifest (16 pods)
└── README.md
```
