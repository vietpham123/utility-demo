# Traffic Controller

A web-based dashboard for managing traffic generators deployed on Kubernetes. Provides start/stop controls, configuration updates, and log viewing for both Browser (Playwright) and Locust traffic generators.

## Features

- **Start / Stop** — Toggle traffic generators on/off (scales deployment replicas 0 ↔ 1)
- **Configuration** — Update concurrent users, navigations per session, and session interval
- **Log Viewer** — View recent pod logs for each generator
- **Auto-refresh** — Dashboard refreshes every 15 seconds
- **Dark Theme** — Styled dashboard with status badges (ON/OFF, Browser/Locust)

## Architecture

```
┌──────────────────────────┐
│   Traffic Controller UI  │ :80 (Ingress)
│   (HTML/JS Dashboard)    │
└────────────┬─────────────┘
             │ REST API
┌────────────▼─────────────┐
│   Express.js Server      │ :8080
│   K8s REST API Client    │
│   (ServiceAccount auth)  │
└────────────┬─────────────┘
             │ K8s API
┌────────────▼─────────────┐
│   Kubernetes API Server  │
│   - Deployments (CRUD)   │
│   - Pods / Logs (read)   │
└──────────────────────────┘
```

## Managed Generators

| ID | Label | Namespace | Deployment |
|---|---|---|---|
| `utility-browser` | Utility — Browser (Playwright) | utility-outage-analytics | browser-traffic-gen |
| `retail-browser` | Retail — Browser (Playwright) | retail | browser-traffic-gen |
| `utility-locust` | Utility — Locust (HTTP) | utility-outage-analytics | load-generator |
| `retail-locust` | Retail — Locust (HTTP) | retail | load-generator |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/generators` | Status of all generators (replicas, config, readiness) |
| `POST` | `/api/generators/:id/toggle` | Toggle generator on/off |
| `POST` | `/api/generators/:id/config` | Update env vars (CONCURRENT_USERS, etc.) |
| `GET` | `/api/generators/:id/logs` | Recent pod logs (tail 80 lines) |

## Build and Deploy

```bash
export REGISTRY=<your-registry>

# Build and push
docker build -t $REGISTRY/traffic-controller:latest .
docker push $REGISTRY/traffic-controller:latest

# Deploy (includes ServiceAccount, ClusterRole, ClusterRoleBinding, Deployment, Service, Ingress)
kubectl apply -f k8s.yaml
```

## RBAC

The app runs with a dedicated ServiceAccount (`traffic-controller-sa`) with a ClusterRole granting:
- `apps/deployments`: get, list, patch, update
- `pods`, `pods/log`: get, list

## Project Structure

```
traffic-controller/
├── server.js          # Express.js backend with K8s REST API client
├── public/
│   └── index.html     # Dark-themed dashboard UI
├── package.json       # Dependencies (express, @kubernetes/client-node)
├── Dockerfile         # node:20-slim based
└── k8s.yaml           # Full K8s manifest (RBAC + Deployment + Service + Ingress)
```
