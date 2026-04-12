"""
GenericUtility UI Navigation Simulator — Locust-based traffic generator.
Emulates real users: login → navigate 10 random pages → logout.
Each page navigation triggers the same API calls the browser makes.

Dynatrace RUM Integration:
- Real browser User-Agent strings so Dynatrace classifies traffic as real users
- Referer headers chain correctly from page to page for user-action detection
- Proper Accept/Accept-Language headers matching browser fingerprints
- Cookie persistence per session for Dynatrace session correlation
- Unique X-Session-Id header per session for server-side session grouping
- X-Forwarded-For for geo-location simulation
"""
import json
import os
import random
import time
import uuid
import logging
from locust import HttpUser, task, between, TaskSet

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
                "storm", "repair", "emergency", "new york", "boston", "atlanta",
                "miami", "dallas", "houston", "nashville", "charlotte", "orlando",
                "detroit", "cleveland", "pittsburgh", "st louis", "minneapolis"]

REGIONS = ["Chicago-Metro", "StLouis-Metro", "Minneapolis-Metro", "Detroit-Metro",
           "Cleveland-Metro", "Pittsburgh-Metro", "Philadelphia-Metro", "Baltimore-Metro",
           "DC-Metro", "NewYork-Metro", "Boston-Metro", "Atlanta-Metro", "Miami-Metro",
           "Dallas-Metro", "Houston-Metro", "Nashville-Metro", "Charlotte-Metro",
           "Orlando-Metro", "Atlantic-Coast", "Delaware-Valley"]

RATE_CLASSES = ["R-1", "R-2", "C-1", "C-2", "I-1"]

# --- Real browser User-Agent strings for Dynatrace RUM detection ---
BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
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

APP_BASE_URL = os.getenv("LOCUST_HOST", "http://analytics-gateway:3000")

MAX_NAVIGATIONS = 10


def think(low=1, high=4):
    """Simulate user reading/thinking time between actions."""
    time.sleep(random.uniform(low, high))


class UISession(TaskSet):
    """
    Simulates a user session: login → navigate 10 random pages → logout.
    Starts at the login page. Each navigation picks a random tab and fires
    the API calls the browser would make. Referer chains correctly from
    page to page for Dynatrace user-action detection.
    """

    def on_start(self):
        """User starts at the login page and authenticates."""
        self.session_id = str(uuid.uuid4())
        self.username = random.choice(DEMO_USERNAMES)
        self.current_page = "/login"
        self.nav_count = 0
        self.token = ""

        # POST login — first action in the session
        with self.client.post("/api/auth/login", json={
            "username": self.username,
            "password": DEMO_PASSWORD
        }, headers=self._browser_headers(),
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

    @task
    def navigate_page(self):
        """Navigate to a random page. After 10 navigations, logout and end session."""
        if self.nav_count >= MAX_NAVIGATIONS:
            if self.token:
                self.client.post("/api/auth/logout",
                                 headers=self._browser_headers(),
                                 name="[Logout] POST /api/auth/logout")
            self.interrupt()
            return

        handler = random.choice([
            self._nav_overview, self._nav_scada, self._nav_outages,
            self._nav_metering, self._nav_grid, self._nav_reliability,
            self._nav_forecast, self._nav_crew, self._nav_notifications,
            self._nav_weather, self._nav_customers, self._nav_pricing,
            self._nav_workorders, self._nav_auditlog, self._nav_alerts,
            self._nav_health, self._nav_search,
        ])
        handler()
        self.nav_count += 1

    # ---- Tab navigation methods ----
    # Each method fires the API calls the browser makes when clicking that tab.
    # Referer is set to self.current_page (the previous page) automatically.
    # current_page is updated AFTER requests so the next navigation has correct Referer.

    def _nav_overview(self):
        h = self._browser_headers()
        self.client.get("/api/dashboard", headers=h, name="[Overview] GET /api/dashboard")
        self.client.get("/api/outages/active", headers=h, name="[Overview] GET /api/outages/active")
        self.client.get("/api/scada/alerts", headers=h, name="[Overview] GET /api/scada/alerts")
        self.client.get("/api/weather/conditions", headers=h, name="[Overview] GET /api/weather/conditions")
        self.client.get("/api/weather/forecast", headers=h, name="[Overview] GET /api/weather/forecast")
        self.client.get("/api/crew/crews", headers=h, name="[Overview] GET /api/crew/crews")
        self.client.get("/api/crew/dispatches/active", headers=h, name="[Overview] GET /api/crew/dispatches/active")
        self.current_page = "/overview"

    def _nav_scada(self):
        h = self._browser_headers()
        self.client.get("/api/scada/summary", headers=h, name="[SCADA] GET /api/scada/summary")
        self.client.get("/api/scada/readings/latest", headers=h, name="[SCADA] GET /api/scada/readings/latest")
        self.client.get("/api/scada/alerts?limit=30", headers=h, name="[SCADA] GET /api/scada/alerts?limit=30")
        self.current_page = "/scada"

    def _nav_outages(self):
        h = self._browser_headers()
        self.client.get("/api/outages/stats/summary", headers=h, name="[Outages] GET /api/outages/stats/summary")
        resp = self.client.get("/api/outages", headers=h, name="[Outages] GET /api/outages")
        self.current_page = "/outages"
        if resp.status_code == 200:
            try:
                outages = resp.json()
                if outages:
                    oid = random.choice(outages).get("id", "OUT-001")
                    self.client.get(f"/api/outages/{oid}",
                                    headers=self._browser_headers(),
                                    name="[Outages] GET /api/outages/[id]")
            except Exception:
                pass

    def _nav_metering(self):
        h = self._browser_headers()
        self.client.get("/api/meter-data/summary", headers=h, name="[Metering] GET /api/meter-data/summary")
        self.client.get("/api/meter-data/readings?limit=50", headers=h, name="[Metering] GET /api/meter-data/readings")
        self.client.get("/api/meter-data/anomalies?limit=30", headers=h, name="[Metering] GET /api/meter-data/anomalies")
        self.current_page = "/metering"

    def _nav_grid(self):
        h = self._browser_headers()
        self.client.get("/api/grid/stats", headers=h, name="[Grid] GET /api/grid/stats")
        self.client.get("/api/grid/topology", headers=h, name="[Grid] GET /api/grid/topology")
        self.current_page = "/grid"

    def _nav_reliability(self):
        h = self._browser_headers()
        self.client.get("/api/reliability/indices", headers=h, name="[Reliability] GET /api/reliability/indices")
        self.client.get("/api/reliability/history?days=30", headers=h, name="[Reliability] GET /api/reliability/history")
        self.current_page = "/reliability"

    def _nav_forecast(self):
        h = self._browser_headers()
        self.client.get("/api/forecast/summary", headers=h, name="[Forecast] GET /api/forecast/summary")
        self.client.get("/api/forecast/current", headers=h, name="[Forecast] GET /api/forecast/current")
        self.client.get("/api/forecast/peak-demand", headers=h, name="[Forecast] GET /api/forecast/peak-demand")
        self.current_page = "/forecast"

    def _nav_crew(self):
        h = self._browser_headers()
        self.client.get("/api/crew/stats", headers=h, name="[Crew] GET /api/crew/stats")
        self.client.get("/api/crew/crews", headers=h, name="[Crew] GET /api/crew/crews")
        self.client.get("/api/crew/dispatches/active", headers=h, name="[Crew] GET /api/crew/dispatches/active")
        self.client.get("/api/crew/dispatches?limit=30", headers=h, name="[Crew] GET /api/crew/dispatches")
        self.current_page = "/crew"

    def _nav_notifications(self):
        h = self._browser_headers()
        self.client.get("/api/notifications/stats", headers=h, name="[Notifications] GET /api/notifications/stats")
        self.client.get("/api/notifications/log?limit=50", headers=h, name="[Notifications] GET /api/notifications/log")
        self.current_page = "/notifications"

    def _nav_weather(self):
        h = self._browser_headers()
        self.client.get("/api/weather/summary", headers=h, name="[Weather] GET /api/weather/summary")
        self.client.get("/api/weather/conditions", headers=h, name="[Weather] GET /api/weather/conditions")
        self.client.get("/api/weather/forecast", headers=h, name="[Weather] GET /api/weather/forecast")
        self.client.get("/api/weather/alerts?limit=30", headers=h, name="[Weather] GET /api/weather/alerts")
        self.client.get("/api/weather/correlations", headers=h, name="[Weather] GET /api/weather/correlations")
        self.current_page = "/weather"

    def _nav_customers(self):
        h = self._browser_headers()
        page = random.randint(1, 5)
        self.client.get(f"/api/customers?page={page}&limit=20", headers=h,
                        name="[Customers] GET /api/customers")
        self.client.get("/api/customers/stats", headers=h,
                        name="[Customers] GET /api/customers/stats")
        self.current_page = "/customers"
        term = random.choice(SEARCH_TERMS[:6])
        self.client.get(f"/api/customers/search?q={term}",
                        headers=self._browser_headers(),
                        name="[Customers] GET /api/customers/search")

    def _nav_pricing(self):
        h = self._browser_headers()
        self.client.get("/api/pricing/current", headers=h, name="[Pricing] GET /api/pricing/current")
        self.client.get("/api/pricing/rates", headers=h, name="[Pricing] GET /api/pricing/rates")
        self.client.get("/api/pricing/regions", headers=h, name="[Pricing] GET /api/pricing/regions")
        self.current_page = "/pricing"
        rc = random.choice(RATE_CLASSES)
        region = random.choice(REGIONS)
        kwh = random.randint(200, 3000)
        self.client.get(f"/api/pricing/calculate?rateClass={rc}&region={region}&kwh={kwh}",
                        headers=self._browser_headers(),
                        name="[Pricing] GET /api/pricing/calculate")

    def _nav_workorders(self):
        h = self._browser_headers()
        page = random.randint(1, 5)
        self.client.get(f"/api/work-orders?page={page}&limit=20", headers=h,
                        name="[WorkOrders] GET /api/work-orders")
        self.client.get("/api/work-orders/stats", headers=h,
                        name="[WorkOrders] GET /api/work-orders/stats")
        self.current_page = "/work-orders"

    def _nav_auditlog(self):
        h = self._browser_headers()
        page = random.randint(1, 5)
        self.client.get(f"/api/audit/log?page={page}&limit=30", headers=h,
                        name="[AuditLog] GET /api/audit/log")
        self.client.get("/api/audit/stats", headers=h,
                        name="[AuditLog] GET /api/audit/stats")
        self.current_page = "/audit"

    def _nav_alerts(self):
        h = self._browser_headers()
        self.client.get("/api/alerts/correlated?limit=30", headers=h,
                        name="[Alerts] GET /api/alerts/correlated")
        self.client.get("/api/alerts/stats", headers=h,
                        name="[Alerts] GET /api/alerts/stats")
        self.current_page = "/alerts"

    def _nav_health(self):
        h = self._browser_headers()
        self.client.get("/api/health", headers=h, name="[Health] GET /api/health")
        self.current_page = "/health"

    def _nav_search(self):
        h = self._browser_headers()
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/search?q={term}", headers=h,
                        name="[Search] GET /api/search")

    def _browser_headers(self, accept="application/json, text/plain, */*"):
        """
        Build headers that match a real browser request so Dynatrace
        detects this as a genuine user session.
        Referer is set to current_page (the page the user is coming FROM).
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
            "X-Session-Id": self.session_id,
            "X-Username": self.username,
            "X-Forwarded-For": self.user.client_ip,
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h


# ============================================================
# User Classes — different browsing speeds
# Each user gets a persistent browser UA + client IP so
# Dynatrace groups all their requests into one session.
# wait_time controls pause between page navigations.
# ============================================================

class CasualBrowser(HttpUser):
    """Casual user — browses slowly, longer pauses between pages."""
    wait_time = between(3, 8)
    weight = 5
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)


class ActiveOperator(HttpUser):
    """Operator actively monitoring — moderate pace."""
    wait_time = between(2, 5)
    weight = 3
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)


class PowerUser(HttpUser):
    """Power user — rapid navigation through pages."""
    wait_time = between(1, 3)
    weight = 2
    tasks = {UISession: 1}

    def on_start(self):
        self.ua = random.choice(BROWSER_USER_AGENTS)
        self.client_ip = random.choice(CLIENT_IPS)
