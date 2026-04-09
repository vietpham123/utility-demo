"""
GenericUtility UI Navigation Simulator — Locust-based traffic generator.
Emulates real users navigating through the web UI: logging in, clicking tabs,
browsing data, using search, and interacting with UI elements.
Each tab click triggers the same API calls the browser makes.
"""
import json
import os
import random
import time
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


def think(low=1, high=4):
    """Simulate user reading/thinking time between actions."""
    time.sleep(random.uniform(low, high))


class UISession(SequentialTaskSet):
    """
    Simulates a full user session: open app → login → browse tabs → logout.
    Each tab triggers the exact same API calls the browser UI makes on navigation.
    """
    token = ""
    user_info = None

    def on_start(self):
        """User opens the app in their browser."""
        self.client.get("/", name="[Page] Load index.html")
        self.client.get("/extensions.js", name="[Page] Load extensions.js")
        think(1, 2)

    # --- Login ---
    @task
    def login(self):
        username = random.choice(DEMO_USERNAMES)
        with self.client.post("/api/auth/login", json={
            "username": username,
            "password": DEMO_PASSWORD
        }, name="[Login] POST /api/auth/login", catch_response=True) as resp:
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
        h = self._headers()
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
        h = self._headers()
        self.client.get("/api/scada/summary", headers=h, name="[SCADA] GET /api/scada/summary")
        self.client.get("/api/scada/readings/latest", headers=h, name="[SCADA] GET /api/scada/readings/latest")
        self.client.get("/api/scada/alerts?limit=30", headers=h, name="[SCADA] GET /api/scada/alerts?limit=30")
        think(3, 8)

    # --- Tab: Outage Management ---
    @task
    def tab_outages(self):
        h = self._headers()
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
                    self.client.get(f"/api/outages/{oid}", headers=h,
                                    name="[Outages] GET /api/outages/[id]")
                    think(2, 4)
            except Exception:
                pass

    # --- Tab: Meter Data ---
    @task
    def tab_metering(self):
        h = self._headers()
        self.client.get("/api/meter-data/summary", headers=h, name="[Metering] GET /api/meter-data/summary")
        self.client.get("/api/meter-data/readings?limit=50", headers=h, name="[Metering] GET /api/meter-data/readings")
        self.client.get("/api/meter-data/anomalies?limit=30", headers=h, name="[Metering] GET /api/meter-data/anomalies")
        think(3, 6)

    # --- Tab: Grid Topology ---
    @task
    def tab_grid(self):
        h = self._headers()
        self.client.get("/api/grid/stats", headers=h, name="[Grid] GET /api/grid/stats")
        self.client.get("/api/grid/topology", headers=h, name="[Grid] GET /api/grid/topology")
        think(3, 6)

    # --- Tab: Reliability Indices ---
    @task
    def tab_reliability(self):
        h = self._headers()
        self.client.get("/api/reliability/indices", headers=h, name="[Reliability] GET /api/reliability/indices")
        self.client.get("/api/reliability/history?days=30", headers=h, name="[Reliability] GET /api/reliability/history")
        think(2, 5)

    # --- Tab: Demand Forecast ---
    @task
    def tab_forecast(self):
        h = self._headers()
        self.client.get("/api/forecast/summary", headers=h, name="[Forecast] GET /api/forecast/summary")
        self.client.get("/api/forecast/current", headers=h, name="[Forecast] GET /api/forecast/current")
        self.client.get("/api/forecast/peak-demand", headers=h, name="[Forecast] GET /api/forecast/peak-demand")
        think(2, 5)

    # --- Tab: Crew Dispatch ---
    @task
    def tab_crew(self):
        h = self._headers()
        self.client.get("/api/crew/stats", headers=h, name="[Crew] GET /api/crew/stats")
        self.client.get("/api/crew/crews", headers=h, name="[Crew] GET /api/crew/crews")
        self.client.get("/api/crew/dispatches/active", headers=h, name="[Crew] GET /api/crew/dispatches/active")
        self.client.get("/api/crew/dispatches?limit=30", headers=h, name="[Crew] GET /api/crew/dispatches")
        think(3, 6)

    # --- Tab: Notifications ---
    @task
    def tab_notifications(self):
        h = self._headers()
        self.client.get("/api/notifications/stats", headers=h, name="[Notifications] GET /api/notifications/stats")
        self.client.get("/api/notifications/log?limit=50", headers=h, name="[Notifications] GET /api/notifications/log")
        think(2, 5)

    # --- Tab: Weather ---
    @task
    def tab_weather(self):
        h = self._headers()
        self.client.get("/api/weather/summary", headers=h, name="[Weather] GET /api/weather/summary")
        self.client.get("/api/weather/conditions", headers=h, name="[Weather] GET /api/weather/conditions")
        self.client.get("/api/weather/forecast", headers=h, name="[Weather] GET /api/weather/forecast")
        self.client.get("/api/weather/alerts?limit=30", headers=h, name="[Weather] GET /api/weather/alerts")
        self.client.get("/api/weather/correlations", headers=h, name="[Weather] GET /api/weather/correlations")
        think(3, 6)

    # --- Tab: Customers ---
    @task
    def tab_customers(self):
        h = self._headers()
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
        h = self._headers()
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
        h = self._headers()
        page = random.randint(1, 5)
        self.client.get(f"/api/work-orders?page={page}&limit=20", headers=h,
                        name="[WorkOrders] GET /api/work-orders")
        self.client.get("/api/work-orders/stats", headers=h,
                        name="[WorkOrders] GET /api/work-orders/stats")
        think(3, 6)

    # --- Tab: Audit Log ---
    @task
    def tab_auditlog(self):
        h = self._headers()
        page = random.randint(1, 5)
        self.client.get(f"/api/audit/log?page={page}&limit=30", headers=h,
                        name="[AuditLog] GET /api/audit/log")
        self.client.get("/api/audit/stats", headers=h,
                        name="[AuditLog] GET /api/audit/stats")
        think(2, 5)

    # --- Tab: Alert Correlation ---
    @task
    def tab_alertcorrelation(self):
        h = self._headers()
        self.client.get("/api/alerts/correlated?limit=30", headers=h,
                        name="[Alerts] GET /api/alerts/correlated")
        self.client.get("/api/alerts/stats", headers=h,
                        name="[Alerts] GET /api/alerts/stats")
        think(3, 6)

    # --- Tab: Service Health ---
    @task
    def tab_health(self):
        h = self._headers()
        self.client.get("/api/health", headers=h, name="[Health] GET /api/health")
        think(2, 4)

    # --- Use global search ---
    @task
    def use_search(self):
        h = self._headers()
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/search?q={term}", headers=h,
                        name="[Search] GET /api/search")
        think(2, 5)

    # --- Logout and end session ---
    @task
    def logout(self):
        if self.token:
            self.client.post("/api/auth/logout",
                             headers=self._headers(),
                             name="[Logout] POST /api/auth/logout")
            self.token = ""
        self.interrupt()

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}


# ============================================================
# User Classes — different browsing patterns
# ============================================================

class CasualBrowser(HttpUser):
    """Casual user — browses a few tabs per session, longer think times."""
    wait_time = between(5, 15)
    weight = 5
    tasks = {UISession: 1}


class ActiveOperator(HttpUser):
    """Operator actively monitoring — faster tab switching."""
    wait_time = between(2, 6)
    weight = 3
    tasks = {UISession: 1}


class PowerUser(HttpUser):
    """Power user — rapid navigation through many tabs."""
    wait_time = between(1, 3)
    weight = 2
    tasks = {UISession: 1}
