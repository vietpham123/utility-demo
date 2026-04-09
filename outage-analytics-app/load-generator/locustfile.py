"""
GenericUtility UI Navigation Simulator — Locust-based traffic generator.
Emulates real users navigating through the web UI: logging in, clicking tabs,
browsing data, using search, and interacting with UI elements.
Each tab click triggers the same API calls the browser makes.

Dynatrace RUM Integration:
- Real browser User-Agent strings so Dynatrace classifies traffic as real users
- Referer headers on every request to enable Dynatrace user-action detection
- Proper Accept/Accept-Language headers matching browser fingerprints
- HTML page loads that trigger Dynatrace JS agent injection (Set-Cookie: dtCookie)
- Cookie persistence per session for Dynatrace session correlation
- Unique x-session-id header per session for server-side session grouping
"""
import json
import os
import random
import time
import uuid
import logging
from locust import HttpUser, task, between, SequentialTaskSet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui-nav")

# Password from env or default
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "utility2026")

# All 15 demo usernames — password is shared
DEMO_USERNAMES = [
    "operator_jones", "engineer_chen", "manager_smith", "analyst_garcia",
    "dispatcher_lee", "supervisor_patel", "technician_wong", "director_johnson",
    "operator_brown", "engineer_martinez", "analyst_taylor", "dispatcher_harris",
    "technician_clark", "manager_lewis", "operator_robinson",
]

SEARCH_TERMS = ["chicago", "baltimore", "philadelphia", "washington", "atlantic",
                "wilmington", "transformer", "feeder", "substation", "outage",
                "storm", "repair", "emergency"]

REGIONS = ["Chicago-Metro", "Baltimore-Metro", "Philadelphia-Metro",
           "DC-Metro", "Atlantic-Coast", "Delaware-Valley"]

RATE_CLASSES = ["R-1", "R-2", "C-1", "C-2", "I-1"]

# --- Real browser User-Agent strings for Dynatrace RUM detection ---
BROWSER_USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    # Chrome on iPad
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1",
]

# Simulated client IP addresses for Dynatrace geo-location
CLIENT_IPS = [
    "73.162.45.112",   # Chicago residential
    "68.134.201.88",   # Baltimore residential
    "24.101.55.200",   # Philadelphia residential
    "71.178.92.44",    # Washington DC residential
    "98.169.118.33",   # Atlanta residential
    "72.83.145.77",    # Wilmington residential
    "50.206.71.129",   # Newark residential
    "75.144.58.201",   # Pittsburgh residential
    "64.134.200.15",   # Richmond residential
    "69.142.88.160",   # Charlotte residential
]

# Base URL for Referer header (set at runtime from host)
APP_BASE_URL = os.getenv("LOCUST_HOST", "http://analytics-gateway:3000")


def think(low=1, high=4):
    """Simulate user reading/thinking time between actions."""
    time.sleep(random.uniform(low, high))


class UISession(SequentialTaskSet):
    """
    Simulates a full user session: open app → login → browse tabs → logout.
    Each tab triggers the exact same API calls the browser UI makes on navigation.

    Dynatrace-aware: sends real browser headers, maintains session cookies,
    includes Referer for user-action detection, and sets x-forwarded-for
    for geo-location.
    """
    token = ""
    user_info = None
    session_id = ""
    username = ""
    current_page = "/"

    def on_start(self):
        """User opens the app in their browser — full page load triggers DT RUM."""
        self.session_id = str(uuid.uuid4())
        self.username = random.choice(DEMO_USERNAMES)
        self.current_page = "/"

        # Load the main HTML page — Dynatrace OneAgent injects JS here
        # and sets dtCookie via Set-Cookie. Locust client persists cookies.
        self.client.get("/", headers=self._browser_headers("/"),
                        name="[Page] Load index.html")
        think(0.3, 0.8)
        # Browser loads JS bundles
        self.client.get("/static/js/main.js",
                        headers=self._browser_headers("/", accept="application/javascript"),
                        name="[Page] Load main.js")
        self.client.get("/static/css/main.css",
                        headers=self._browser_headers("/", accept="text/css"),
                        name="[Page] Load main.css")
        think(1, 2)

    # --- Login ---
    @task
    def login(self):
        self.current_page = "/login"
        with self.client.post("/api/auth/login", json={
            "username": self.username,
            "password": DEMO_PASSWORD
        }, headers=self._browser_headers("/login"),
           name="[Login] POST /api/auth/login", catch_response=True) as resp:
            if resp.status_code == 200:
                try:
                    self.token = resp.json().get("token", "")
                    resp.success()
                except Exception:
                    self.token = ""
                    resp.failure("Bad login response")
            else:
                self.token = ""
                resp.failure(f"Login HTTP {resp.status_code}")
        think(1, 2)

    # --- Tab: Overview (default landing) ---
    @task
    def tab_overview(self):
        self.current_page = "/overview"
        h = self._browser_headers("/overview")
        self.client.get("/api/dashboard", headers=h, name="[Overview] GET /api/dashboard")
        self.client.get("/api/outages/active", headers=h, name="[Overview] GET /api/outages/active")
        self.client.get("/api/scada/alerts", headers=h, name="[Overview] GET /api/scada/alerts")
        self.client.get("/api/weather/conditions", headers=h, name="[Overview] GET /api/weather/conditions")
        self.client.get("/api/weather/forecast", headers=h, name="[Overview] GET /api/weather/forecast")
        self.client.get("/api/crew/crews", headers=h, name="[Overview] GET /api/crew/crews")
        self.client.get("/api/crew/dispatches/active", headers=h, name="[Overview] GET /api/crew/dispatches/active")
        think(3, 7)

    # --- Tab: SCADA Telemetry ---
    @task
    def tab_scada(self):
        self.current_page = "/scada"
        h = self._browser_headers("/scada")
        self.client.get("/api/scada/summary", headers=h, name="[SCADA] GET /api/scada/summary")
        self.client.get("/api/scada/readings/latest", headers=h, name="[SCADA] GET /api/scada/readings/latest")
        self.client.get("/api/scada/alerts?limit=30", headers=h, name="[SCADA] GET /api/scada/alerts?limit=30")
        think(3, 8)

    # --- Tab: Outage Management ---
    @task
    def tab_outages(self):
        self.current_page = "/outages"
        h = self._browser_headers("/outages")
        self.client.get("/api/outages/stats/summary", headers=h, name="[Outages] GET /api/outages/stats/summary")
        resp = self.client.get("/api/outages", headers=h, name="[Outages] GET /api/outages")
        think(2, 5)
        # User clicks on an outage row to view details
        if resp.status_code == 200:
            try:
                outages = resp.json()
                if outages and len(outages) > 0:
                    o = random.choice(outages)
                    oid = o.get("id", "OUT-001")
                    self.current_page = f"/outages/{oid}"
                    self.client.get(f"/api/outages/{oid}",
                                    headers=self._browser_headers(f"/outages/{oid}"),
                                    name="[Outages] GET /api/outages/[id]")
                    think(2, 4)
            except Exception:
                pass

    # --- Tab: Meter Data ---
    @task
    def tab_metering(self):
        self.current_page = "/metering"
        h = self._browser_headers("/metering")
        self.client.get("/api/meter-data/summary", headers=h, name="[Metering] GET /api/meter-data/summary")
        self.client.get("/api/meter-data/readings?limit=50", headers=h, name="[Metering] GET /api/meter-data/readings")
        self.client.get("/api/meter-data/anomalies?limit=30", headers=h, name="[Metering] GET /api/meter-data/anomalies")
        think(3, 6)

    # --- Tab: Grid Topology ---
    @task
    def tab_grid(self):
        self.current_page = "/grid"
        h = self._browser_headers("/grid")
        self.client.get("/api/grid/stats", headers=h, name="[Grid] GET /api/grid/stats")
        self.client.get("/api/grid/topology", headers=h, name="[Grid] GET /api/grid/topology")
        think(3, 6)

    # --- Tab: Reliability Indices ---
    @task
    def tab_reliability(self):
        self.current_page = "/reliability"
        h = self._browser_headers("/reliability")
        self.client.get("/api/reliability/indices", headers=h, name="[Reliability] GET /api/reliability/indices")
        self.client.get("/api/reliability/history?days=30", headers=h, name="[Reliability] GET /api/reliability/history")
        think(2, 5)

    # --- Tab: Demand Forecast ---
    @task
    def tab_forecast(self):
        self.current_page = "/forecast"
        h = self._browser_headers("/forecast")
        self.client.get("/api/forecast/summary", headers=h, name="[Forecast] GET /api/forecast/summary")
        self.client.get("/api/forecast/current", headers=h, name="[Forecast] GET /api/forecast/current")
        self.client.get("/api/forecast/peak-demand", headers=h, name="[Forecast] GET /api/forecast/peak-demand")
        think(2, 5)

    # --- Tab: Crew Dispatch ---
    @task
    def tab_crew(self):
        self.current_page = "/crew"
        h = self._browser_headers("/crew")
        self.client.get("/api/crew/stats", headers=h, name="[Crew] GET /api/crew/stats")
        self.client.get("/api/crew/crews", headers=h, name="[Crew] GET /api/crew/crews")
        self.client.get("/api/crew/dispatches/active", headers=h, name="[Crew] GET /api/crew/dispatches/active")
        self.client.get("/api/crew/dispatches?limit=30", headers=h, name="[Crew] GET /api/crew/dispatches")
        think(3, 6)

    # --- Tab: Notifications ---
    @task
    def tab_notifications(self):
        self.current_page = "/notifications"
        h = self._browser_headers("/notifications")
        self.client.get("/api/notifications/stats", headers=h, name="[Notifications] GET /api/notifications/stats")
        self.client.get("/api/notifications/log?limit=50", headers=h, name="[Notifications] GET /api/notifications/log")
        think(2, 5)

    # --- Tab: Weather ---
    @task
    def tab_weather(self):
        self.current_page = "/weather"
        h = self._browser_headers("/weather")
        self.client.get("/api/weather/summary", headers=h, name="[Weather] GET /api/weather/summary")
        self.client.get("/api/weather/conditions", headers=h, name="[Weather] GET /api/weather/conditions")
        self.client.get("/api/weather/forecast", headers=h, name="[Weather] GET /api/weather/forecast")
        self.client.get("/api/weather/alerts?limit=30", headers=h, name="[Weather] GET /api/weather/alerts")
        self.client.get("/api/weather/correlations", headers=h, name="[Weather] GET /api/weather/correlations")
        think(3, 6)

    # --- Tab: Customers ---
    @task
    def tab_customers(self):
        self.current_page = "/customers"
        h = self._browser_headers("/customers")
        page = random.randint(1, 5)
        self.client.get(f"/api/customers?page={page}&limit=20", headers=h,
                        name="[Customers] GET /api/customers")
        self.client.get("/api/customers/stats", headers=h,
                        name="[Customers] GET /api/customers/stats")
        think(2, 4)
        # User searches for a customer
        term = random.choice(SEARCH_TERMS[:6])
        self.client.get(f"/api/customers/search?q={term}", headers=h,
                        name="[Customers] GET /api/customers/search")
        think(2, 4)

    # --- Tab: Pricing ---
    @task
    def tab_pricing(self):
        self.current_page = "/pricing"
        h = self._browser_headers("/pricing")
        self.client.get("/api/pricing/current", headers=h, name="[Pricing] GET /api/pricing/current")
        self.client.get("/api/pricing/rates", headers=h, name="[Pricing] GET /api/pricing/rates")
        self.client.get("/api/pricing/regions", headers=h, name="[Pricing] GET /api/pricing/regions")
        think(2, 5)
        # User calculates a rate
        rc = random.choice(RATE_CLASSES)
        region = random.choice(REGIONS)
        kwh = random.randint(200, 3000)
        self.client.get(f"/api/pricing/calculate?rateClass={rc}&region={region}&kwh={kwh}",
                        headers=h, name="[Pricing] GET /api/pricing/calculate")
        think(2, 4)

    # --- Tab: Work Orders ---
    @task
    def tab_workorders(self):
        self.current_page = "/work-orders"
        h = self._browser_headers("/work-orders")
        page = random.randint(1, 5)
        self.client.get(f"/api/work-orders?page={page}&limit=20", headers=h,
                        name="[WorkOrders] GET /api/work-orders")
        self.client.get("/api/work-orders/stats", headers=h,
                        name="[WorkOrders] GET /api/work-orders/stats")
        think(3, 6)

    # --- Tab: Audit Log ---
    @task
    def tab_auditlog(self):
        self.current_page = "/audit"
        h = self._browser_headers("/audit")
        page = random.randint(1, 5)
        self.client.get(f"/api/audit/log?page={page}&limit=30", headers=h,
                        name="[AuditLog] GET /api/audit/log")
        self.client.get("/api/audit/stats", headers=h,
                        name="[AuditLog] GET /api/audit/stats")
        think(2, 5)

    # --- Tab: Alert Correlation ---
    @task
    def tab_alertcorrelation(self):
        self.current_page = "/alerts"
        h = self._browser_headers("/alerts")
        self.client.get("/api/alerts/correlated?limit=30", headers=h,
                        name="[Alerts] GET /api/alerts/correlated")
        self.client.get("/api/alerts/stats", headers=h,
                        name="[Alerts] GET /api/alerts/stats")
        think(3, 6)

    # --- Tab: Service Health ---
    @task
    def tab_health(self):
        self.current_page = "/health"
        h = self._browser_headers("/health")
        self.client.get("/api/health", headers=h, name="[Health] GET /api/health")
        think(2, 4)

    # --- Use global search ---
    @task
    def use_search(self):
        h = self._browser_headers(self.current_page)
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/search?q={term}", headers=h,
                        name="[Search] GET /api/search")
        think(2, 5)

    # --- Logout and end session ---
    @task
    def logout(self):
        if self.token:
            self.client.post("/api/auth/logout",
                             headers=self._browser_headers("/logout"),
                             name="[Logout] POST /api/auth/logout")
            self.token = ""
        self.interrupt()

    def _browser_headers(self, page="/", accept="application/json, text/plain, */*"):
        """
        Build headers that match a real browser request so Dynatrace
        detects this as a genuine user session.
        """
        h = {
            "User-Agent": self.user.ua,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"{APP_BASE_URL}{self.current_page}",
            "Origin": APP_BASE_URL,
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            # Session identification for Dynatrace server-side session grouping
            "X-Session-Id": self.session_id,
            "X-Username": self.username,
            # Simulated client IP for Dynatrace geo-location detection
            "X-Forwarded-For": self.user.client_ip,
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h


# ============================================================
# User Classes — different browsing patterns
# Each user gets a persistent browser UA + client IP to ensure
# Dynatrace groups all their requests into one session.
# ============================================================

class CasualBrowser(HttpUser):
    """Casual user — browses a few tabs per session, longer think times."""
    wait_time = between(5, 15)
    weight = 5
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)


class ActiveOperator(HttpUser):
    """Operator actively monitoring — faster tab switching."""
    wait_time = between(2, 6)
    weight = 3
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)


class PowerUser(HttpUser):
    """Power user — rapid navigation through many tabs."""
    wait_time = between(1, 3)
    weight = 2
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)
