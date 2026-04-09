/// Alert Correlation Service (Rust/Actix-web)
/// Correlates SCADA alerts + weather data + outage events to produce correlated alerts
/// Adds Rust to polyglot mix (like AstroShop's Shipping service)
/// Calls weather-service and outage-service for data enrichment
use actix_web::{web, App, HttpServer, HttpResponse, middleware};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use chrono::Utc;
use uuid::Uuid;
use rand::Rng;
use log::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CorrelatedAlert {
    id: String,
    timestamp: String,
    alert_type: String,
    severity: String,
    region: String,
    source_alerts: Vec<String>,
    weather_related: bool,
    correlation_score: f64,
    primary_factor: String,
    risk_level: String,
    recommended_action: String,
    weather_context: Option<serde_json::Value>,
    outage_context: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CorrelateRequest {
    scada_alert_id: Option<String>,
    region: Option<String>,
    alert_type: Option<String>,
}

struct AppState {
    alerts: Mutex<Vec<CorrelatedAlert>>,
    weather_url: String,
    outage_url: String,
}

const REGIONS: &[&str] = &["Chicago-Metro", "Baltimore-Metro", "Philadelphia-Metro", "DC-Metro", "Atlantic-Coast", "Delaware-Valley"];
const ALERT_TYPES: &[&str] = &["voltage_anomaly", "frequency_deviation", "overload", "equipment_failure", "power_quality", "phase_imbalance"];
const SEVERITIES: &[&str] = &["Low", "Moderate", "High", "Critical"];
const FACTORS: &[&str] = &["High wind speed exceeding threshold", "Temperature-induced equipment stress",
    "Lightning strike correlation", "Heavy precipitation impact", "Ice accumulation on lines",
    "Vegetation contact during storm", "Equipment age degradation", "Load spike correlation"];
const ACTIONS: &[&str] = &["Monitor closely for 15 minutes", "Dispatch inspection crew",
    "Activate storm response protocol", "Notify operations center", "Pre-position emergency crew",
    "Initiate load shedding evaluation", "Schedule preventive maintenance", "Escalate to engineering"];

fn generate_initial_alerts() -> Vec<CorrelatedAlert> {
    let mut rng = rand::thread_rng();
    (0..50).map(|_| {
        let score: f64 = rng.gen_range(15.0..98.0);
        let severity = if score > 80.0 { "Critical" } else if score > 60.0 { "High" } else if score > 40.0 { "Moderate" } else { "Low" };
        let risk = if score > 75.0 { "Critical" } else if score > 50.0 { "High" } else if score > 25.0 { "Medium" } else { "Low" };
        CorrelatedAlert {
            id: format!("COR-{}", &Uuid::new_v4().to_string()[..8]),
            timestamp: Utc::now().to_rfc3339(),
            alert_type: ALERT_TYPES[rng.gen_range(0..ALERT_TYPES.len())].to_string(),
            severity: severity.to_string(),
            region: REGIONS[rng.gen_range(0..REGIONS.len())].to_string(),
            source_alerts: vec![
                format!("SCADA-{:03}", rng.gen_range(1..100)),
                format!("WX-{:03}", rng.gen_range(1..50)),
            ],
            weather_related: score > 45.0,
            correlation_score: (score * 10.0).round() / 10.0,
            primary_factor: FACTORS[rng.gen_range(0..FACTORS.len())].to_string(),
            risk_level: risk.to_string(),
            recommended_action: ACTIONS[rng.gen_range(0..ACTIONS.len())].to_string(),
            weather_context: None,
            outage_context: None,
        }
    }).collect()
}

async fn get_alerts(data: web::Data<AppState>, query: web::Query<std::collections::HashMap<String, String>>) -> HttpResponse {
    let alerts = data.alerts.lock().unwrap();
    let page: usize = query.get("page").and_then(|p| p.parse().ok()).unwrap_or(1);
    let limit: usize = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(30);
    let severity = query.get("severity");
    let region = query.get("region");

    let mut filtered: Vec<&CorrelatedAlert> = alerts.iter().rev().collect();
    if let Some(s) = severity { filtered.retain(|a| &a.severity == s); }
    if let Some(r) = region { filtered.retain(|a| a.region.contains(r.as_str())); }

    let total = filtered.len();
    let offset = (page - 1) * limit;
    let results: Vec<&CorrelatedAlert> = filtered.into_iter().skip(offset).take(limit).collect();

    HttpResponse::Ok().json(serde_json::json!({
        "alerts": results,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) / limit
    }))
}

async fn get_stats(data: web::Data<AppState>) -> HttpResponse {
    let alerts = data.alerts.lock().unwrap();
    let total = alerts.len();
    let weather_related = alerts.iter().filter(|a| a.weather_related).count();
    let critical = alerts.iter().filter(|a| a.risk_level == "Critical").count();
    let high = alerts.iter().filter(|a| a.risk_level == "High").count();
    let avg_score: f64 = if total > 0 { alerts.iter().map(|a| a.correlation_score).sum::<f64>() / total as f64 } else { 0.0 };

    HttpResponse::Ok().json(serde_json::json!({
        "totalAlerts": total,
        "weatherRelated": weather_related,
        "criticalRisk": critical,
        "highRisk": high,
        "avgCorrelationScore": (avg_score * 10.0).round() / 10.0,
        "byRegion": count_by_field(&alerts, |a| &a.region),
        "bySeverity": count_by_field(&alerts, |a| &a.severity),
        "byAlertType": count_by_field(&alerts, |a| &a.alert_type),
    }))
}

fn count_by_field(alerts: &[CorrelatedAlert], f: fn(&CorrelatedAlert) -> &String) -> serde_json::Value {
    let mut map = std::collections::HashMap::new();
    for a in alerts { *map.entry(f(a).clone()).or_insert(0u32) += 1; }
    serde_json::to_value(map).unwrap()
}

async fn correlate(data: web::Data<AppState>, body: web::Json<CorrelateRequest>) -> HttpResponse {
    let region = body.region.clone().unwrap_or_else(|| REGIONS[rand::thread_rng().gen_range(0..REGIONS.len())].to_string());
    info!("Correlating alert for region: {}", region);

    // Hop 1: Fetch weather data from weather-service
    let weather_context = match reqwest::Client::new()
        .get(format!("{}/api/weather/region/{}", data.weather_url, region))
        .timeout(std::time::Duration::from_secs(5))
        .send().await {
        Ok(resp) => resp.json::<serde_json::Value>().await.ok(),
        Err(e) => { info!("Weather fetch failed: {}", e); None }
    };

    // Hop 2: Fetch active outages from outage-service
    let outage_context = match reqwest::Client::new()
        .get(format!("{}/api/outages/active", data.outage_url))
        .timeout(std::time::Duration::from_secs(5))
        .send().await {
        Ok(resp) => resp.json::<serde_json::Value>().await.ok(),
        Err(e) => { info!("Outage fetch failed: {}", e); None }
    };

    let mut rng = rand::thread_rng();
    let score: f64 = rng.gen_range(20.0..95.0);
    let severity = if score > 80.0 { "Critical" } else if score > 60.0 { "High" } else if score > 40.0 { "Moderate" } else { "Low" };

    let alert = CorrelatedAlert {
        id: format!("COR-{}", &Uuid::new_v4().to_string()[..8]),
        timestamp: Utc::now().to_rfc3339(),
        alert_type: body.alert_type.clone().unwrap_or_else(|| ALERT_TYPES[rng.gen_range(0..ALERT_TYPES.len())].to_string()),
        severity: severity.to_string(),
        region: region.clone(),
        source_alerts: vec![
            body.scada_alert_id.clone().unwrap_or_else(|| format!("SCADA-{:03}", rng.gen_range(1..100))),
            format!("WX-{:03}", rng.gen_range(1..50)),
        ],
        weather_related: score > 45.0,
        correlation_score: (score * 10.0).round() / 10.0,
        primary_factor: FACTORS[rng.gen_range(0..FACTORS.len())].to_string(),
        risk_level: if score > 75.0 { "Critical" } else if score > 50.0 { "High" } else { "Medium" }.to_string(),
        recommended_action: ACTIONS[rng.gen_range(0..ACTIONS.len())].to_string(),
        weather_context,
        outage_context,
    };

    data.alerts.lock().unwrap().push(alert.clone());
    // Keep bounded
    let mut alerts = data.alerts.lock().unwrap();
    while alerts.len() > 5000 { alerts.remove(0); }

    HttpResponse::Created().json(alert)
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "Healthy",
        "service": "alert-correlation-service",
        "language": "Rust",
        "timestamp": Utc::now().to_rfc3339()
    }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    info!("Alert Correlation Service (Rust/Actix) starting on port 8070");

    let state = web::Data::new(AppState {
        alerts: Mutex::new(generate_initial_alerts()),
        weather_url: std::env::var("WEATHER_SERVICE_URL").unwrap_or_else(|_| "http://weather-service:8080".to_string()),
        outage_url: std::env::var("OUTAGE_SERVICE_URL").unwrap_or_else(|_| "http://outage-service:3000".to_string()),
    });

    // Background correlation simulator
    let bg_state = state.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
            let req = CorrelateRequest {
                scada_alert_id: Some(format!("SCADA-{:03}", rand::thread_rng().gen_range(1..100))),
                region: Some(REGIONS[rand::thread_rng().gen_range(0..REGIONS.len())].to_string()),
                alert_type: Some(ALERT_TYPES[rand::thread_rng().gen_range(0..ALERT_TYPES.len())].to_string()),
            };
            correlate(bg_state.clone(), web::Json(req)).await;
        }
    });

    HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            .route("/api/alerts/correlated", web::get().to(get_alerts))
            .route("/api/alerts/stats", web::get().to(get_stats))
            .route("/api/alerts/correlate", web::post().to(correlate))
            .route("/api/alerts/health", web::get().to(health))
    })
    .bind("0.0.0.0:8070")?
    .run()
    .await
}
