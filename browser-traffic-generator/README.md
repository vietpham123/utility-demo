# Browser Traffic Generator

A Playwright-based headless Chromium traffic generator that creates real browser sessions detectable by Dynatrace RUM (Real User Monitoring). Unlike HTTP-based tools like Locust, this generator runs an actual browser that executes JavaScript — including the Dynatrace JS agent — producing genuine user sessions with page actions, XHR tracking, and click events.

## How It Works

1. Launches headless Chromium via Playwright
2. Opens concurrent browser sessions (each with a fresh context = fresh DT session)
3. Each session: **Login → Navigate N random pages → Logout → Wait → Repeat**
4. The Dynatrace OneAgent JS snippet injected by the web server runs in the real browser, so all page loads, XHRs, and user actions appear as authentic user sessions

## Modes

| Mode | Description |
|---|---|
| `utility` | Navigates the Utility Outage Analytics dashboard (18 hash-based sections) |
| `retail` | Navigates the Retail Management app (Material UI tabs with Select dropdown login) |
| `generic` | **App-agnostic** — discovers navigation elements via CSS selectors (configurable via env vars) |

## Environment Variables

### Common (all modes)

| Variable | Default | Description |
|---|---|---|
| `APP_MODE` | `utility` | `utility`, `retail`, or `generic` |
| `APP_URL` | auto | Base URL of the web application |
| `CONCURRENT_USERS` | `3` | Number of parallel browser sessions |
| `NAVIGATIONS_PER_SESSION` | `10` | Pages to visit per session cycle |
| `SESSION_INTERVAL` | `60` | Seconds between session cycles (with random jitter) |

### Generic Mode Only

| Variable | Default | Description |
|---|---|---|
| `NAV_SELECTOR` | `nav a, [role='tab'], .nav button` | CSS selector to discover clickable navigation elements |
| `LOGIN_USER_SELECTOR` | _(empty)_ | CSS selector for the username input field |
| `LOGIN_PASS_SELECTOR` | _(empty)_ | CSS selector for the password input field |
| `LOGIN_SUBMIT_SELECTOR` | _(empty)_ | CSS selector for the login submit button |
| `LOGIN_USERNAME` | _(empty)_ | Username to enter at login |
| `LOGIN_PASSWORD` | _(empty)_ | Password to enter at login |
| `LOGOUT_SELECTOR` | _(empty)_ | CSS selector for the logout button |

## Build and Deploy

### Docker Build

```bash
export REGISTRY=<your-registry>
docker build -t $REGISTRY/browser-traffic-gen:latest .
docker push $REGISTRY/browser-traffic-gen:latest
```

### Kubernetes Deployment

Three manifest templates are provided:

| File | Mode | Target |
|---|---|---|
| `k8s-utility.yaml` | utility | Utility Outage Analytics app |
| `k8s-retail.yaml` | retail | Retail Management app |
| `k8s-generic.yaml` | generic | Any web application (template) |

```bash
# Deploy for a specific app
kubectl apply -f k8s-utility.yaml
# or
kubectl apply -f k8s-retail.yaml
# or customize k8s-generic.yaml and apply
kubectl apply -f k8s-generic.yaml
```

### Enable / Disable

```bash
# Stop generating traffic
kubectl scale deployment/browser-traffic-gen -n <namespace> --replicas=0

# Start generating traffic
kubectl scale deployment/browser-traffic-gen -n <namespace> --replicas=1
```

## Generic Mode Example

To use with any web application, set `APP_MODE=generic` and configure the CSS selectors:

```yaml
env:
- name: APP_MODE
  value: "generic"
- name: APP_URL
  value: "https://myapp.example.com"
- name: NAV_SELECTOR
  value: "nav a, .sidebar-link, [role='tab']"
- name: LOGIN_USER_SELECTOR
  value: "#username"
- name: LOGIN_PASS_SELECTOR
  value: "#password"
- name: LOGIN_SUBMIT_SELECTOR
  value: "button[type='submit']"
- name: LOGIN_USERNAME
  value: "demo_user"
- name: LOGIN_PASSWORD
  value: "demo_pass"
- name: LOGOUT_SELECTOR
  value: "button:has-text('Logout')"
```

## Project Structure

```
browser-traffic-generator/
├── generator.js       # Main Playwright traffic generator (utility/retail/generic)
├── package.json       # Node.js dependencies (playwright 1.52.0)
├── Dockerfile         # Based on mcr.microsoft.com/playwright:v1.52.0-noble
├── k8s-utility.yaml   # K8s deployment for utility app
├── k8s-retail.yaml    # K8s deployment for retail app
└── k8s-generic.yaml   # K8s deployment template for any app
```

## Requirements

- **Docker image base**: `mcr.microsoft.com/playwright:v1.52.0-noble` (includes Chromium 136)
- **Resources**: 512Mi–1Gi RAM, 250m–1000m CPU per pod
- **Network**: Pod must be able to reach the target web app URL
- **Dynatrace**: OneAgent must be injecting the JS agent into the target web app for RUM session detection
