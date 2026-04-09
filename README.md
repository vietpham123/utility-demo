# GenericUtility — Utility Management Platform

A multi-tier, polyglot utility management platform designed for Kubernetes deployment with observability. The platform consists of two applications simulating real-world utility operations: customer billing and outage analytics.

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            Kubernetes Cluster                              │
│                                                                            │
│  ┌─── Customer Billing ──────────┐  ┌─── Outage Analytics ────────────────┐│
│  │                               │  │                                     ││
│  │  ┌──────────┐                 │  │  ┌──────────┐   ┌────────────────┐  ││
│  │  │Billing UI│ ← Ingress/LB    │  │  │Analytics │ ← Ingress/LB       │  ││
│  │  │ (nginx)  │                 │  │  │UI (nginx)│                    │  ││
│  │  └────┬─────┘                 │  │  └────┬─────┘                    │  ││
│  │       │                       │  │       │                          │  ││
│  │  ┌────▼──────────┐            │  │  ┌────▼──────────────────────┐   │  ││
│  │  │Billing Gateway│            │  │  │  Analytics Gateway        │   │  ││
│  │  │  (.NET 6)     │            │  │  │  (Node.js/Express)        │   │  ││
│  │  └──┬───┬───┬────┘            │  │  └──┬──┬──┬──┬──┬──┬──┬──┬──┘    │  ││
│  │     │   │   │                 │  │     │  │  │  │  │  │  │  │  │    │  ││
│  │  ┌──▼┐┌─▼─┐┌▼──┐              │  │  16 microservices (see below)    │  ││
│  │  │Cus││Inv││Pay│              │  │                                  │  ││
│  │  │tom││oic││men│              │  │  ┌──────────────────────────┐    │  ││
│  │  │er ││e  ││t  │              │  │  │ TimescaleDB │ Redis      │    │  ││
│  │  │.NE││.NE││.NE│              │  │  │ Kafka       │ RabbitMQ   │    │  ││
│  │  │T 6││T 6││T 6│              │  │  └──────────────────────────┘    │  ││
│  │  └───┘└───┘└───┘              │  │                                  │  ││
│  └───────────────────────────────┘  └──────────────────────────────────┘  ││
│                                                                            │
│  Dynatrace OneAgent (auto-injected on all pods)                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Applications

| Application | Pods | Languages |
|---|---|---|
| [Customer Billing](customer-billing-app/) | 5 (3 microservices + gateway + UI) | .NET 6 |
| [Outage Analytics](outage-analytics-app/) | 24 (16 microservices + gateway + UI + 4 infra + reverse-proxy + load-generator) | Node.js, .NET 6, Java 17, Python, Go, Ruby, Kotlin, PHP, Elixir, Rust |

## Technology Stack

| Layer | Technologies |
|---|---|
| **Languages** | C# (.NET 6), Java 17 (Spring Boot), Node.js (Express), Python (Flask), Go, Ruby (Sinatra), Kotlin (Ktor), PHP, Elixir (Phoenix), Rust (Actix) |
| **Protocols** | HTTP/REST, gRPC, WebSocket, AMQP |
| **Databases** | TimescaleDB (PostgreSQL) |
| **Caching** | Redis |
| **Messaging** | Apache Kafka (KRaft mode), RabbitMQ |
| **Container Runtime** | Docker, Kubernetes |
| **Observability** | Dynatrace OneAgent (auto-injection) |
| **UI** | Nginx + Vanilla JS SPA |

## Infrastructure

| Component | Purpose |
|---|---|
| **Kubernetes Cluster** | Container orchestration |
| **Container Registry** | Image storage (ACR, Docker Hub, etc.) |
| **Build Host** | VM for Docker builds and image pushes |
| **DNS / Ingress** | TLS termination and routing |

## Deployment

### Prerequisites

- Kubernetes cluster (1.26+)
- Container registry access
- `kubectl` configured
- Docker for building images

### Build and Deploy

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

# Deploy to Kubernetes
kubectl apply -f k8s/all-in-one.yaml
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n <your-namespace>

# Check external access
kubectl get svc -A | grep LoadBalancer
```

## Repository Structure

```
├── customer-billing-app/
│   ├── gateway/           # .NET 6 API gateway
│   ├── services/
│   │   ├── customer-service/   # .NET 6 — customer CRUD
│   │   ├── invoice-service/    # .NET 6 — invoice management
│   │   └── payment-service/    # .NET 6 — payment processing
│   ├── ui-web/            # Nginx SPA
│   └── k8s/               # Kubernetes manifests
│
├── outage-analytics-app/
│   ├── gateway/           # Node.js API gateway + simulation orchestrator
│   ├── reverse-proxy/     # NGINX reverse proxy
│   ├── load-generator/    # Locust traffic simulator
│   ├── services/
│   │   ├── outage-service/          # Node.js — outage tracking
│   │   ├── usage-service/           # Node.js — energy usage
│   │   ├── grid-topology-service/   # Node.js — grid network model
│   │   ├── demand-forecast-service/ # Node.js — load forecasting
│   │   ├── crew-dispatch-service/   # Node.js — crew dispatch + WebSocket
│   │   ├── scada-service/           # .NET 6 — SCADA telemetry
│   │   ├── meter-data-service/      # Java 17 — smart meter data (MDMS)
│   │   ├── reliability-service/     # Python — IEEE 1366 indices
│   │   ├── notification-service/    # Python — multi-channel alerts
│   │   ├── weather-service/         # Go — weather correlation
│   │   ├── customer-service/        # Ruby — customer management + auth
│   │   ├── aggregator-service/      # Node.js — cross-service aggregation
│   │   ├── audit-service/           # Kotlin — audit trail
│   │   ├── pricing-service/         # PHP — rate calculations
│   │   ├── work-order-service/      # Elixir — work order lifecycle
│   │   └── alert-correlation-service/ # Rust — multi-signal correlation
│   ├── ui-web/            # Nginx SPA (dark-themed dashboard)
│   └── k8s/               # Kubernetes manifests
│
└── README.md              # This file
```

## Fault Injection / Feature Flags

The platform includes a built-in fault injection engine for demo and testing. Faults can be toggled via the **Feature Flags** tab in the Analytics UI or via the API.

### Available Scenarios

| Scenario | Failure Rate | Affected Services | Description |
|---|---|---|---|
| `database-outage` | 80% | outage, usage, reliability, meter-data | Database connection pool exhausted |
| `cascade-failure` | 70% | scada, outage, grid, reliability, crew | SCADA timeout cascading across services |
| `resource-exhaustion` | 65% | meter-data, reliability, forecast, weather | OOM / thread pool exhaustion on Java/Python services |
| `network-partition` | 85% | crew, notifications, scada, outage | Kafka + RabbitMQ broker connectivity lost |

### UI Toggle

1. Open the Analytics UI
2. Click the **⚙ Feature Flags** tab in the navigation bar
3. Toggle any scenario on/off — the status bar shows live error counts and elapsed time
4. Click **Clear All Faults** to return to normal

### API

```bash
# Enable a fault scenario
curl -X POST http://<APP_ENDPOINT>/api/fault/inject \
  -H "Content-Type: application/json" \
  -d '{"scenario":"database-outage"}'

# Enable with custom failure rate (0.0 – 1.0)
curl -X POST http://<APP_ENDPOINT>/api/fault/inject \
  -H "Content-Type: application/json" \
  -d '{"scenario":"cascade-failure", "failureRate": 0.90}'

# Check current status
curl http://<APP_ENDPOINT>/api/fault/status

# Clear all faults
curl -X POST http://<APP_ENDPOINT>/api/fault/clear \
  -H "Content-Type: application/json" -d '{}'
```

### How It Works

When enabled, the gateway middleware intercepts requests to affected service routes and returns real HTTP 500/502/503/504 errors with infrastructure-realistic error messages. The gateway also propagates fault mode to backend services so observability tools see failures at both the gateway and individual service levels.
