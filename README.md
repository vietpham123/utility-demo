# GenericUtility — Utility Management Platform

A multi-tier, polyglot utility management platform deployed on Azure Kubernetes Service (AKS) with full Dynatrace observability. The platform consists of two applications simulating real-world utility operations: customer billing and outage analytics.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AKS Cluster (VPAKSeasytrade)                        │
│                                                                              │
│  ┌─── utility-customer-billing ───┐  ┌─── utility-outage-analytics ────────┐│
│  │                                │  │                                      ││
│  │  ┌──────────┐                  │  │  ┌──────────┐   ┌────────────────┐  ││
│  │  │Billing UI│ ← LoadBalancer   │  │  │Analytics │ ← LoadBalancer     │  ││
│  │  │ (nginx)  │                  │  │  │UI (nginx)│                    │  ││
│  │  └────┬─────┘                  │  │  └────┬─────┘                    │  ││
│  │       │                        │  │       │                          │  ││
│  │  ┌────▼──────────┐             │  │  ┌────▼──────────────────────┐   │  ││
│  │  │Billing Gateway│             │  │  │  Analytics Gateway        │   │  ││
│  │  │  (.NET 6)     │             │  │  │  (Node.js/Express)        │   │  ││
│  │  └──┬───┬───┬────┘             │  │  └──┬──┬──┬──┬──┬──┬──┬──┬──┘   │  ││
│  │     │   │   │                  │  │     │  │  │  │  │  │  │  │  │   │  ││
│  │  ┌──▼┐┌─▼─┐┌▼──┐              │  │  10 microservices (see below)    │  ││
│  │  │Cus││Inv││Pay│              │  │                                  │  ││
│  │  │tom││oic││men│              │  │  ┌──────────────────────────┐    │  ││
│  │  │er ││e  ││t  │              │  │  │ TimescaleDB │ Redis      │    │  ││
│  │  │.NE││.NE││.NE│              │  │  │ Kafka       │ RabbitMQ   │    │  ││
│  │  │T 6││T 6││T 6│              │  │  └──────────────────────────┘    │  ││
│  │  └───┘└───┘└───┘              │  │                                  │  ││
│  └────────────────────────────────┘  └──────────────────────────────────┘  ││
│                                                                              │
│  Dynatrace OneAgent (auto-injected on all pods)                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Applications

| Application | Namespace | Services | Languages | Access |
|---|---|---|---|---|
| [Customer Billing](customer-billing-app/) | `utility-customer-billing` | 5 (3 microservices + gateway + UI) | .NET 6 | http://40.124.209.164 |
| [Outage Analytics](outage-analytics-app/) | `utility-outage-analytics` | 16 (10 microservices + gateway + UI + 4 infra) | Node.js, .NET 6, Java 17, Python 3.11, Go 1.22 | http://20.165.22.240 |

## Technology Stack

| Layer | Technologies |
|---|---|
| **Languages** | C# (.NET 6), Java 17 (Spring Boot 3.2), Node.js 18 (Express), Python 3.11 (Flask), Go 1.22 |
| **Protocols** | HTTP/REST, gRPC, WebSocket, AMQP |
| **Databases** | TimescaleDB (PostgreSQL 15) |
| **Caching** | Redis 7 |
| **Messaging** | Apache Kafka (KRaft mode), RabbitMQ 3.13 |
| **Container Runtime** | Docker, AKS (Kubernetes 1.31) |
| **Registry** | Azure Container Registry (`vietregistry.azurecr.io`) |
| **Observability** | Dynatrace OneAgent (auto-injection) |
| **UI** | Nginx + Vanilla JS SPA |

## Infrastructure

| Component | Details |
|---|---|
| **AKS Cluster** | `VPAKSeasytrade`, Resource Group `VPEtrade_group` |
| **VM** | `52.248.43.42` (build host, SSH key `VPET_key.pem`) |
| **ACR** | `vietregistry.azurecr.io` |
| **Node Pool** | Standard_D4ds_v5 |

## Deployment

### Prerequisites

- Azure CLI with AKS credentials configured
- Docker installed on the build VM
- SSH access to `52.248.43.42` with `~/.ssh/VPET_key.pem`
- ACR login: `az acr login --name vietregistry`

### Build and Deploy

```bash
# SSH into build VM
ssh -i ~/.ssh/VPET_key.pem azureuser@52.248.43.42

# Build all images (from ~/outage-analytics-app or ~/customer-billing-app)
ACR=vietregistry.azurecr.io

# Analytics services (example for each language)
docker build -t $ACR/outage-service:latest services/outage-service/      # Node.js
docker build -t $ACR/scada-service:latest services/scada-service/        # .NET 6
docker build -t $ACR/meter-data-service:latest services/meter-data-service/  # Java 17
docker build -t $ACR/reliability-service:latest services/reliability-service/ # Python 3.11
docker build -t $ACR/weather-service:latest services/weather-service/    # Go 1.22
docker build -t $ACR/analytics-gateway:latest gateway/
docker build -t $ACR/analytics-ui:latest ui-web/

# Push to ACR
docker push $ACR/<image-name>:latest

# Deploy to AKS
kubectl apply -f k8s/all-in-one.yaml
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n utility-outage-analytics
kubectl get pods -n utility-customer-billing

# Check external access
kubectl get svc -A | grep LoadBalancer

# Test simulation cycle (analytics)
kubectl exec deploy/analytics-gateway -n utility-outage-analytics -- \
  wget -qO- http://localhost:3000/api/simulate/cycle
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
│   ├── services/
│   │   ├── outage-service/        # Node.js — outage tracking
│   │   ├── usage-service/         # Node.js — energy usage
│   │   ├── grid-topology-service/ # Node.js — grid network model
│   │   ├── demand-forecast-service/ # Node.js — load forecasting
│   │   ├── crew-dispatch-service/ # Node.js — crew dispatch + WebSocket
│   │   ├── scada-service/         # .NET 6 — SCADA telemetry
│   │   ├── meter-data-service/    # Java 17 — smart meter data (MDMS)
│   │   ├── reliability-service/   # Python 3.11 — IEEE 1366 indices
│   │   ├── notification-service/  # Python 3.11 — multi-channel alerts
│   │   └── weather-service/       # Go 1.22 — weather correlation + gRPC
│   ├── ui-web/            # Nginx SPA (dark-themed dashboard)
│   └── k8s/               # Kubernetes manifests
│
└── README.md              # This file
```
