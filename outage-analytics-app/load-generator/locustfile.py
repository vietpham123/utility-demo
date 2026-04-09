"""
Load Generator — Simulates realistic user traffic for Dynatrace RUM + distributed traces.
Mimics user behavior: login → browse dashboard → search outages → create work orders → export reports.
Uses Locust for continuous traffic generation (like AstroShop/EasyTrade load generators).
"""
import json
import random
import time
import logging
from locust import HttpUser, task, between, SequentialTaskSet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loadgen")

DEMO_USERS = [
    {"username": "operator_jones", "password": "utility2026", "name": "Sarah Jones", "role": "operator"},
    {"username": "engineer_chen", "password": "utility2026", "name": "David Chen", "role": "engineer"},
    {"username": "manager_smith", "password": "utility2026", "name": "Michael Smith", "role": "manager"},
    {"username": "analyst_garcia", "password": "utility2026", "name": "Maria Garcia", "role": "analyst"},
    {"username": "dispatcher_lee", "password": "utility2026", "name": "James Lee", "role": "dispatcher"},
]

SEARCH_TERMS = ["chicago", "baltimore", "philadelphia", "washington", "atlantic", "wilmington",
                "transformer", "feeder", "substation", "critical", "high", "storm"]

REGIONS = ["Chicago-Metro", "Baltimore-Metro", "Philadelphia-Metro", "DC-Metro",
           "Atlantic-Coast", "Delaware-Valley"]


class DashboardBrowsingFlow(SequentialTaskSet):
    """Simulates a user logging in and browsing the dashboard"""

    def on_start(self):
        self.user_info = random.choice(DEMO_USERS)
        # Login
        resp = self.client.post("/api/auth/login", json={
            "username": self.user_info["username"],
            "password": self.user_info["password"]
        }, name="/api/auth/login", catch_response=True)
        if resp.status_code == 200:
            try:
                data = resp.json()
                self.token = data.get("token", "")
                resp.success()
            except Exception:
                self.token = ""
                resp.success()
        else:
            self.token = ""
            resp.success()

    @task
    def view_dashboard(self):
        """Phase 1: Load main dashboard (aggregated view)"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/aggregate/dashboard", headers=headers, name="/api/aggregate/dashboard")
        time.sleep(random.uniform(1, 3))

    @task
    def view_outages(self):
        """Phase 2: Check active outages"""
        self.client.get("/api/outages/active", name="/api/outages/active")
        self.client.get("/api/outages/stats/summary", name="/api/outages/stats/summary")
        time.sleep(random.uniform(0.5, 2))

    @task
    def view_scada(self):
        """Phase 3: Check SCADA telemetry"""
        self.client.get("/api/scada/summary", name="/api/scada/summary")
        self.client.get("/api/scada/readings/latest", name="/api/scada/readings/latest")
        self.client.get("/api/scada/alerts?limit=20", name="/api/scada/alerts")
        time.sleep(random.uniform(0.5, 1.5))

    @task
    def view_weather(self):
        """Phase 4: Check weather conditions"""
        self.client.get("/api/weather/summary", name="/api/weather/summary")
        self.client.get("/api/weather/conditions", name="/api/weather/conditions")
        self.client.get("/api/weather/forecast", name="/api/weather/forecast")
        time.sleep(random.uniform(1, 2))

    @task
    def check_crew(self):
        """Phase 5: Check crew status"""
        self.client.get("/api/crew/stats", name="/api/crew/stats")
        self.client.get("/api/crew/crews", name="/api/crew/crews")
        self.client.get("/api/crew/dispatches/active", name="/api/crew/dispatches/active")
        time.sleep(random.uniform(0.5, 1.5))

    @task
    def stop(self):
        self.interrupt()


class SearchAndDrilldownFlow(SequentialTaskSet):
    """Simulates searching for outages and drilling into details"""

    @task
    def search_outages(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/search?q={term}&type=outages", name="/api/search")
        time.sleep(random.uniform(1, 2))

    @task
    def search_customers(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/api/search?q={term}&type=customers", name="/api/search")
        time.sleep(random.uniform(0.5, 1.5))

    @task
    def view_outage_enriched(self):
        """Deep enrichment — triggers 6-hop trace through aggregator"""
        # Get outages first, then drill into one
        resp = self.client.get("/api/outages/active", name="/api/outages/active")
        if resp.status_code == 200:
            try:
                outages = resp.json()
                if outages and len(outages) > 0:
                    outage_id = random.choice(outages).get("id", "OUT-001")
                    self.client.get(f"/api/aggregate/outage/{outage_id}",
                                    name="/api/aggregate/outage/[id]")
                    time.sleep(random.uniform(1, 3))
            except Exception:
                pass

    @task
    def view_correlation(self):
        """Full correlation — 7-service sequential chain"""
        self.client.get("/api/aggregate/correlation", name="/api/aggregate/correlation")
        time.sleep(random.uniform(2, 4))

    @task
    def stop(self):
        self.interrupt()


class WorkOrderFlow(SequentialTaskSet):
    """Simulates creating and managing work orders"""

    @task
    def get_work_orders(self):
        self.client.get("/api/work-orders", name="/api/work-orders")
        time.sleep(random.uniform(1, 2))

    @task
    def create_work_order(self):
        region = random.choice(REGIONS)
        self.client.post("/api/work-orders", json={
            "outageId": f"OUT-{random.randint(1, 50):03d}",
            "type": random.choice(["repair", "inspection", "maintenance", "emergency"]),
            "priority": random.choice(["critical", "high", "medium", "low"]),
            "region": region,
            "description": f"Work order for {region} area",
            "estimatedHours": random.randint(1, 8)
        }, name="/api/work-orders [POST]")
        time.sleep(random.uniform(1, 3))

    @task
    def stop(self):
        self.interrupt()


class ReportExportFlow(SequentialTaskSet):
    """Simulates generating and exporting reports"""

    @task
    def generate_outage_report(self):
        self.client.get("/api/aggregate/report/outages", name="/api/aggregate/report/outages")
        time.sleep(random.uniform(2, 4))

    @task
    def generate_reliability_report(self):
        self.client.get("/api/aggregate/report/reliability", name="/api/aggregate/report/reliability")
        time.sleep(random.uniform(2, 4))

    @task
    def generate_crew_report(self):
        self.client.get("/api/aggregate/report/crew", name="/api/aggregate/report/crew")
        time.sleep(random.uniform(1, 3))

    @task
    def stop(self):
        self.interrupt()


class HealthCheckFlow(SequentialTaskSet):
    """Periodically checks service health"""

    @task
    def check_health(self):
        self.client.get("/api/health", name="/api/health")
        time.sleep(random.uniform(3, 5))

    @task
    def check_fault_status(self):
        self.client.get("/api/fault/status", name="/api/fault/status")
        time.sleep(random.uniform(2, 3))

    @task
    def check_pricing(self):
        self.client.get("/api/pricing/current", name="/api/pricing/current")
        time.sleep(random.uniform(1, 2))

    @task
    def stop(self):
        self.interrupt()


class OperatorUser(HttpUser):
    """Primary user type — browses dashboard, searches, manages work orders"""
    wait_time = between(2, 8)
    weight = 5

    tasks = {
        DashboardBrowsingFlow: 4,
        SearchAndDrilldownFlow: 3,
        WorkOrderFlow: 2,
        ReportExportFlow: 1,
    }


class AnalystUser(HttpUser):
    """Analyst user — focuses on reports and correlations"""
    wait_time = between(3, 10)
    weight = 3

    tasks = {
        DashboardBrowsingFlow: 2,
        SearchAndDrilldownFlow: 4,
        ReportExportFlow: 3,
        HealthCheckFlow: 1,
    }


class MonitorUser(HttpUser):
    """Passive monitoring user — checks health and dashboards"""
    wait_time = between(5, 15)
    weight = 2

    tasks = {
        DashboardBrowsingFlow: 5,
        HealthCheckFlow: 3,
    }
