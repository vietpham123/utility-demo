# Customer Billing Platform

A .NET 6 microservices application for utility customer billing, invoice management, and payment processing. Deployed on AKS with Dynatrace OneAgent.

**Access:** http://40.124.209.164  
**Namespace:** `utility-customer-billing`

## Architecture

```
            ┌──────────────────────────┐
            │   Billing UI (Nginx)     │ :80 (LoadBalancer)
            │   Customer Portal SPA    │
            └────────────┬─────────────┘
                         │
            ┌────────────▼─────────────┐
            │   Billing Gateway        │ :80
            │   (.NET 6 Web API)       │
            │   + DataSimulatorService │
            └──┬─────────┬─────────┬───┘
               │         │         │
     ┌─────────▼──┐ ┌────▼─────┐ ┌▼──────────┐
     │ Customer   │ │ Invoice  │ │ Payment   │
     │ Service    │ │ Service  │ │ Service   │
     │ .NET 6     │ │ .NET 6   │ │ .NET 6    │
     │ :80        │ │ :80      │ │ :80       │
     └────────────┘ └──────────┘ └───────────┘
```

## Services

| Service | Framework | Port | Replicas | Description |
|---|---|---|---|---|
| **billing-gateway** | .NET 6 Web API | 80 | 2 | API gateway with DataSimulatorService for data generation |
| **customer-service** | .NET 6 Web API | 80 | 2 | Customer account CRUD operations |
| **invoice-service** | .NET 6 Web API | 80 | 2 | Bill generation and invoice history |
| **payment-service** | .NET 6 Web API | 80 | 2 | Payment processing (simulated) |
| **billing-ui** | Nginx | 80 | 2 | Customer-facing SPA portal |

All services use in-memory data (no external database).

## API Endpoints

| Gateway Route | Upstream |
|---|---|
| `GET /api/gateway/customers` | customer-service `/api/customers` |
| `GET /api/gateway/invoices` | invoice-service `/api/invoices` |
| `GET /api/gateway/payments` | payment-service `/api/payments` |
| `POST /api/gateway/simulate` | Triggers data simulation cycle |
| `GET /api/gateway/health` | Gateway health check |

## Build and Deploy

```bash
ssh -i ~/.ssh/VPET_key.pem azureuser@52.248.43.42
cd ~/customer-billing-app
ACR=vietregistry.azurecr.io

# Build all images
docker build -t $ACR/customer-service:latest services/customer-service/
docker build -t $ACR/invoice-service:latest services/invoice-service/
docker build -t $ACR/payment-service:latest services/payment-service/
docker build -t $ACR/billing-gateway:latest gateway/
docker build -t $ACR/billing-ui:latest ui-web/

# Push and deploy
for img in customer-service invoice-service payment-service billing-gateway billing-ui; do
  docker push $ACR/$img:latest
done

kubectl apply -f k8s/all-in-one.yaml
```

## Structure

```
├── gateway/              # .NET 6 API gateway + DataSimulatorService
│   ├── GatewayController.cs
│   ├── Program.cs
│   ├── gateway.csproj
│   └── Dockerfile
├── services/
│   ├── customer-service/  # .NET 6 — customer CRUD
│   ├── invoice-service/   # .NET 6 — invoice management
│   └── payment-service/   # .NET 6 — payment processing
├── ui-web/                # Nginx SPA (billing portal)
├── k8s/
│   └── all-in-one.yaml    # Full deployment manifest (5 pods, 2 replicas each)
└── README.md
```
