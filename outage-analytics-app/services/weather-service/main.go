package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	"github.com/streadway/amqp"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// ============================================================
// Weather Correlation Service — Go + gRPC + HTTP
// Simulates NWS weather data, correlates storms with outages,
// triggers storm-mode alerts via RabbitMQ
// ============================================================

var (
	logger       *zap.Logger
	db           *sql.DB
	rabbitConn   *amqp.Connection
	rabbitCh     *amqp.Channel
	mu           sync.RWMutex
	requestCount int64
	errorCount   int64
)

// ============================================================
// Data models
// ============================================================

type WeatherConditions struct {
	Temperature       float64 `json:"temperatureF"`
	Humidity          float64 `json:"humidityPct"`
	WindSpeed         float64 `json:"windSpeedMph"`
	WindDirection     string  `json:"windDirection"`
	BarometricPressure float64 `json:"barometricPressureInHg"`
	Precipitation     float64 `json:"precipitationIn"`
	Condition         string  `json:"condition"`
	Severity          string  `json:"severity"`
	Visibility        float64 `json:"visibilityMi"`
	LightningDensity  float64 `json:"lightningDensity"`
	Timestamp         string  `json:"timestamp"`
	Location          string  `json:"location"`
}

type StormForecast struct {
	Region                    string  `json:"region"`
	StormType                 string  `json:"stormType"`
	Severity                  string  `json:"severity"`
	ProbabilityPct            float64 `json:"probabilityPct"`
	ExpectedWindMph           float64 `json:"expectedWindMph"`
	ExpectedPrecipitationIn   float64 `json:"expectedPrecipitationIn"`
	ExpectedStart             string  `json:"expectedStart"`
	ExpectedEnd               string  `json:"expectedEnd"`
	EstimatedOutages          int     `json:"estimatedOutages"`
	EstimatedCustomersAffected int    `json:"estimatedCustomersAffected"`
	StormModeActive           bool    `json:"stormModeActive"`
}

type WeatherAlert struct {
	AlertID          string  `json:"alertId"`
	AlertType        string  `json:"alertType"`
	Severity         string  `json:"severity"`
	Region           string  `json:"region"`
	Message          string  `json:"message"`
	IssuedAt         string  `json:"issuedAt"`
	ExpiresAt        string  `json:"expiresAt"`
	WindSpeedMph     float64 `json:"windSpeedMph"`
	StormModeTrigger bool    `json:"stormModeTrigger"`
}

type CorrelationResult struct {
	OutageID            string           `json:"outageId"`
	WeatherRelated      bool             `json:"weatherRelated"`
	PrimaryFactor       string           `json:"primaryFactor"`
	CorrelationScore    float64          `json:"correlationScore"`
	ConditionsAtTime    WeatherConditions `json:"conditionsAtTime"`
	RiskLevel           string           `json:"riskLevel"`
	ContributingFactors []string         `json:"contributingFactors"`
}

type RegionWeather struct {
	Conditions   WeatherConditions `json:"conditions"`
	Forecast     StormForecast     `json:"forecast"`
	ActiveAlerts []WeatherAlert    `json:"activeAlerts"`
	RiskScore    float64           `json:"riskScore"`
}

// ============================================================
// Regions and weather simulation data
// ============================================================

type Region struct {
	Name      string
	City      string
	State     string
	Latitude  float64
	Longitude float64
}

var regions = []Region{
	{Name: "Chicago-Metro", City: "Chicago", State: "IL", Latitude: 41.8781, Longitude: -87.6298},
	{Name: "Baltimore-Metro", City: "Baltimore", State: "MD", Latitude: 39.2904, Longitude: -76.6122},
	{Name: "Philadelphia-Metro", City: "Philadelphia", State: "PA", Latitude: 39.9526, Longitude: -75.1652},
	{Name: "DC-Metro", City: "Washington", State: "DC", Latitude: 38.9072, Longitude: -77.0369},
	{Name: "Atlantic-Coast", City: "Atlantic City", State: "NJ", Latitude: 39.3643, Longitude: -74.4229},
	{Name: "Delaware-Valley", City: "Wilmington", State: "DE", Latitude: 39.7391, Longitude: -75.5398},
}

var stormTypes = []string{"Thunderstorm", "Ice Storm", "Nor'easter", "Derecho", "Tropical Storm", "Heat Wave", "Winter Storm"}
var windDirections = []string{"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
var conditions = []string{"Clear", "Partly Cloudy", "Overcast", "Light Rain", "Heavy Rain", "Thunderstorm", "Ice/Sleet", "Snow", "Fog", "High Winds"}

var regionWeather = make(map[string]*RegionWeather)
var alerts []WeatherAlert
var alertCounter int
var correlationHistory []CorrelationResult

func initLogger() {
	config := zap.Config{
		Level:       zap.NewAtomicLevelAt(zapcore.DebugLevel),
		Development: false,
		Encoding:    "json",
		EncoderConfig: zapcore.EncoderConfig{
			TimeKey:        "timestamp",
			LevelKey:       "level",
			NameKey:        "logger",
			CallerKey:      "caller",
			MessageKey:     "message",
			StacktraceKey:  "stacktrace",
			LineEnding:     zapcore.DefaultLineEnding,
			EncodeLevel:    zapcore.LowercaseLevelEncoder,
			EncodeTime:     zapcore.ISO8601TimeEncoder,
			EncodeDuration: zapcore.MillisDurationEncoder,
			EncodeCaller:   zapcore.ShortCallerEncoder,
		},
		OutputPaths:      []string{"stdout"},
		ErrorOutputPaths: []string{"stderr"},
	}
	var err error
	logger, err = config.Build()
	if err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	logger = logger.With(zap.String("service", "weather-service"))
}

func connectDB() {
	host := getEnv("DB_HOST", "timescaledb")
	port := getEnv("DB_PORT", "5432")
	dbname := getEnv("DB_NAME", "utilitydb")
	user := getEnv("DB_USER", "utilityuser")
	password := getEnv("DB_PASSWORD", "<DB_PASSWORD>")

	connStr := fmt.Sprintf("host=%s port=%s dbname=%s user=%s password=%s sslmode=disable", host, port, dbname, user, password)
	var err error
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		logger.Warn("Database connection failed", zap.Error(err))
		return
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)

	// Create weather tables
	_, err = db.Exec(`
		CREATE SCHEMA IF NOT EXISTS weather;
		CREATE TABLE IF NOT EXISTS weather.observations (
			id SERIAL PRIMARY KEY,
			region VARCHAR(50),
			temperature_f DOUBLE PRECISION,
			humidity_pct DOUBLE PRECISION,
			wind_speed_mph DOUBLE PRECISION,
			wind_direction VARCHAR(5),
			barometric_pressure DOUBLE PRECISION,
			precipitation_in DOUBLE PRECISION,
			condition VARCHAR(50),
			severity VARCHAR(20),
			lightning_density DOUBLE PRECISION,
			recorded_at TIMESTAMPTZ DEFAULT NOW()
		);
		CREATE TABLE IF NOT EXISTS weather.storm_correlations (
			id SERIAL PRIMARY KEY,
			outage_id VARCHAR(20),
			weather_related BOOLEAN,
			primary_factor VARCHAR(100),
			correlation_score DOUBLE PRECISION,
			risk_level VARCHAR(20),
			correlated_at TIMESTAMPTZ DEFAULT NOW()
		);
	`)
	if err != nil {
		logger.Warn("Table creation issue", zap.Error(err))
	} else {
		logger.Info("Database tables ready")
	}
}

func connectRabbitMQ() {
	url := getEnv("RABBITMQ_URL", "amqp://utility:<DB_PASSWORD>@rabbitmq:5672")
	var err error
	rabbitConn, err = amqp.Dial(url)
	if err != nil {
		logger.Warn("RabbitMQ connection failed, running without broker", zap.Error(err))
		return
	}
	rabbitCh, err = rabbitConn.Channel()
	if err != nil {
		logger.Warn("RabbitMQ channel creation failed", zap.Error(err))
		return
	}
	rabbitCh.ExchangeDeclare("weather.events", "topic", true, false, false, false, nil)
	rabbitCh.QueueDeclare("weather.alerts", true, false, false, false, nil)
	rabbitCh.QueueDeclare("weather.storm-mode", true, false, false, false, nil)
	rabbitCh.QueueBind("weather.alerts", "weather.alert.*", "weather.events", false, nil)
	rabbitCh.QueueBind("weather.storm-mode", "weather.storm.activated", "weather.events", false, nil)
	logger.Info("RabbitMQ connected — weather exchanges and queues ready")
}

func publishWeatherEvent(routingKey string, data interface{}) {
	if rabbitCh == nil {
		return
	}
	body, _ := json.Marshal(data)
	err := rabbitCh.Publish("weather.events", routingKey, false, false, amqp.Publishing{
		ContentType: "application/json",
		Body:        body,
	})
	if err != nil {
		logger.Error("Failed to publish weather event", zap.String("routingKey", routingKey), zap.Error(err))
	} else {
		logger.Debug("Published weather event", zap.String("routingKey", routingKey))
	}
}

// ============================================================
// Weather simulation
// ============================================================

func generateWeather(region Region) WeatherConditions {
	hour := time.Now().Hour()
	// Base temperature varies by time of day (sinusoidal)
	baseTemp := 55.0 + 20.0*math.Sin(float64(hour-6)*math.Pi/12.0)
	temp := baseTemp + (rand.Float64()-0.5)*15.0

	windSpeed := 5.0 + rand.Float64()*25.0
	humidity := 30.0 + rand.Float64()*60.0
	pressure := 29.5 + rand.Float64()*1.5
	precip := 0.0
	lightning := 0.0
	visibility := 10.0

	// Determine condition based on parameters
	condition := "Clear"
	severity := "None"

	if humidity > 75 && rand.Float64() < 0.4 {
		condition = "Light Rain"
		precip = rand.Float64() * 0.5
		severity = "Low"
		visibility = 5.0 + rand.Float64()*5.0
	}
	if windSpeed > 20 && humidity > 80 && rand.Float64() < 0.3 {
		condition = "Heavy Rain"
		precip = 0.5 + rand.Float64()*2.0
		severity = "Moderate"
		visibility = 1.0 + rand.Float64()*3.0
	}
	if windSpeed > 25 && rand.Float64() < 0.15 {
		condition = "Thunderstorm"
		precip = 1.0 + rand.Float64()*3.0
		lightning = rand.Float64() * 10.0
		severity = "High"
		visibility = 0.5 + rand.Float64()*2.0
	}
	if temp < 32 && humidity > 70 && rand.Float64() < 0.2 {
		condition = "Ice/Sleet"
		precip = 0.1 + rand.Float64()*0.5
		severity = "High"
		visibility = 1.0 + rand.Float64()*3.0
	}
	if windSpeed > 35 {
		condition = "High Winds"
		severity = "High"
	}

	return WeatherConditions{
		Temperature:        math.Round(temp*10) / 10,
		Humidity:           math.Round(humidity*10) / 10,
		WindSpeed:          math.Round(windSpeed*10) / 10,
		WindDirection:      windDirections[rand.Intn(len(windDirections))],
		BarometricPressure: math.Round(pressure*100) / 100,
		Precipitation:      math.Round(precip*100) / 100,
		Condition:          condition,
		Severity:           severity,
		Visibility:         math.Round(visibility*10) / 10,
		LightningDensity:   math.Round(lightning*10) / 10,
		Timestamp:          time.Now().UTC().Format(time.RFC3339),
		Location:           region.City + ", " + region.State,
	}
}

func generateStormForecast(region Region, conditions WeatherConditions) StormForecast {
	stormProb := 10.0
	if conditions.WindSpeed > 20 {
		stormProb += 25.0
	}
	if conditions.Humidity > 80 {
		stormProb += 20.0
	}
	if conditions.BarometricPressure < 29.8 {
		stormProb += 15.0
	}
	if conditions.LightningDensity > 3 {
		stormProb += 20.0
	}
	stormProb = math.Min(stormProb, 95.0)

	stormType := "None"
	severity := "None"
	estimatedOutages := 0
	estimatedCustomers := 0
	stormMode := false

	if stormProb > 50 {
		stormType = stormTypes[rand.Intn(len(stormTypes))]
		if stormProb > 80 {
			severity = "Severe"
			estimatedOutages = 5 + rand.Intn(20)
			estimatedCustomers = 500 + rand.Intn(5000)
			stormMode = true
		} else if stormProb > 65 {
			severity = "Moderate"
			estimatedOutages = 2 + rand.Intn(10)
			estimatedCustomers = 100 + rand.Intn(2000)
		} else {
			severity = "Minor"
			estimatedOutages = 1 + rand.Intn(5)
			estimatedCustomers = 50 + rand.Intn(500)
		}
	}

	expectedWind := conditions.WindSpeed * (1.0 + rand.Float64()*0.5)
	expectedPrecip := conditions.Precipitation * (1.0 + rand.Float64()*2.0)

	return StormForecast{
		Region:                     region.Name,
		StormType:                  stormType,
		Severity:                   severity,
		ProbabilityPct:             math.Round(stormProb*10) / 10,
		ExpectedWindMph:            math.Round(expectedWind*10) / 10,
		ExpectedPrecipitationIn:    math.Round(expectedPrecip*100) / 100,
		ExpectedStart:              time.Now().Add(time.Duration(2+rand.Intn(6)) * time.Hour).UTC().Format(time.RFC3339),
		ExpectedEnd:                time.Now().Add(time.Duration(8+rand.Intn(16)) * time.Hour).UTC().Format(time.RFC3339),
		EstimatedOutages:           estimatedOutages,
		EstimatedCustomersAffected: estimatedCustomers,
		StormModeActive:            stormMode,
	}
}

func updateAllRegions() {
	mu.Lock()
	defer mu.Unlock()

	for _, region := range regions {
		conditions := generateWeather(region)
		forecast := generateStormForecast(region, conditions)

		rw := &RegionWeather{
			Conditions:   conditions,
			Forecast:     forecast,
			ActiveAlerts: []WeatherAlert{},
			RiskScore:    calculateRiskScore(conditions, forecast),
		}

		// Generate alerts for severe conditions
		if conditions.Severity == "High" || forecast.StormModeActive {
			alertCounter++
			alert := WeatherAlert{
				AlertID:          fmt.Sprintf("WX-ALERT-%04d", alertCounter),
				AlertType:        forecast.StormType,
				Severity:         conditions.Severity,
				Region:           region.Name,
				Message:          fmt.Sprintf("%s warning for %s - Wind: %.1f mph, Precip: %.2f in", forecast.StormType, region.City, conditions.WindSpeed, conditions.Precipitation),
				IssuedAt:         time.Now().UTC().Format(time.RFC3339),
				ExpiresAt:        time.Now().Add(4 * time.Hour).UTC().Format(time.RFC3339),
				WindSpeedMph:     conditions.WindSpeed,
				StormModeTrigger: forecast.StormModeActive,
			}
			rw.ActiveAlerts = append(rw.ActiveAlerts, alert)
			alerts = append(alerts, alert)

			publishWeatherEvent("weather.alert."+strings.ToLower(conditions.Severity), alert)
			if forecast.StormModeActive {
				publishWeatherEvent("weather.storm.activated", map[string]interface{}{
					"region": region.Name, "forecast": forecast, "alert": alert,
				})
				logger.Warn("STORM MODE ACTIVATED",
					zap.String("region", region.Name),
					zap.String("stormType", forecast.StormType),
					zap.Int("estimatedOutages", forecast.EstimatedOutages),
				)
			}
		}

		regionWeather[region.Name] = rw

		// Persist observation to DB
		if db != nil {
			_, err := db.Exec(`INSERT INTO weather.observations (region, temperature_f, humidity_pct, wind_speed_mph, wind_direction, barometric_pressure, precipitation_in, condition, severity, lightning_density)
				VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
				region.Name, conditions.Temperature, conditions.Humidity, conditions.WindSpeed,
				conditions.WindDirection, conditions.BarometricPressure, conditions.Precipitation,
				conditions.Condition, conditions.Severity, conditions.LightningDensity)
			if err != nil {
				logger.Debug("Failed to persist observation", zap.Error(err))
			}
		}
	}

	// Trim alerts
	if len(alerts) > 500 {
		alerts = alerts[len(alerts)-500:]
	}

	logger.Debug("Weather data updated for all regions", zap.Int("regions", len(regions)))
}

func calculateRiskScore(conditions WeatherConditions, forecast StormForecast) float64 {
	score := 0.0
	if conditions.WindSpeed > 15 {
		score += (conditions.WindSpeed - 15) * 2
	}
	if conditions.LightningDensity > 0 {
		score += conditions.LightningDensity * 5
	}
	if conditions.Precipitation > 0.5 {
		score += conditions.Precipitation * 10
	}
	if conditions.Visibility < 3 {
		score += (3 - conditions.Visibility) * 5
	}
	if conditions.Temperature < 32 && conditions.Precipitation > 0 {
		score += 30 // Icing risk
	}
	score += forecast.ProbabilityPct * 0.3
	return math.Min(math.Round(score*10)/10, 100.0)
}

func correlateOutageWithWeather(outageID, location string, lat, lng float64) CorrelationResult {
	// Find nearest region
	var nearestRegion *Region
	minDist := math.MaxFloat64
	for i, r := range regions {
		dist := math.Sqrt(math.Pow(r.Latitude-lat, 2) + math.Pow(r.Longitude-lng, 2))
		if dist < minDist {
			minDist = dist
			nearestRegion = &regions[i]
		}
	}

	mu.RLock()
	rw, ok := regionWeather[nearestRegion.Name]
	mu.RUnlock()

	if !ok {
		return CorrelationResult{
			OutageID:       outageID,
			WeatherRelated: false,
			PrimaryFactor:  "No weather data available",
			RiskLevel:      "Unknown",
		}
	}

	conditions := rw.Conditions
	factors := []string{}
	score := 0.0

	if conditions.WindSpeed > 25 {
		factors = append(factors, fmt.Sprintf("High winds (%.1f mph)", conditions.WindSpeed))
		score += 30
	}
	if conditions.LightningDensity > 2 {
		factors = append(factors, fmt.Sprintf("Lightning activity (%.1f strikes/km²)", conditions.LightningDensity))
		score += 25
	}
	if conditions.Precipitation > 1.0 {
		factors = append(factors, fmt.Sprintf("Heavy precipitation (%.2f in)", conditions.Precipitation))
		score += 20
	}
	if conditions.Temperature < 32 && conditions.Precipitation > 0 {
		factors = append(factors, "Ice accumulation risk")
		score += 35
	}
	if conditions.Visibility < 2 {
		factors = append(factors, fmt.Sprintf("Low visibility (%.1f mi)", conditions.Visibility))
		score += 10
	}

	weatherRelated := score > 25
	primaryFactor := "Equipment failure (non-weather)"
	riskLevel := "Low"
	if score > 60 {
		riskLevel = "Critical"
		primaryFactor = factors[0]
	} else if score > 40 {
		riskLevel = "High"
		primaryFactor = factors[0]
	} else if score > 25 {
		riskLevel = "Moderate"
		primaryFactor = factors[0]
	}

	result := CorrelationResult{
		OutageID:            outageID,
		WeatherRelated:      weatherRelated,
		PrimaryFactor:       primaryFactor,
		CorrelationScore:    math.Min(math.Round(score*10)/10, 100.0),
		ConditionsAtTime:    conditions,
		RiskLevel:           riskLevel,
		ContributingFactors: factors,
	}

	// Persist correlation
	if db != nil {
		db.Exec(`INSERT INTO weather.storm_correlations (outage_id, weather_related, primary_factor, correlation_score, risk_level)
			VALUES ($1,$2,$3,$4,$5)`, outageID, weatherRelated, primaryFactor, score, riskLevel)
	}

	mu.Lock()
	correlationHistory = append(correlationHistory, result)
	if len(correlationHistory) > 500 {
		correlationHistory = correlationHistory[len(correlationHistory)-500:]
	}
	mu.Unlock()

	return result
}

// ============================================================
// HTTP Handlers
// ============================================================

func handleSimulate(w http.ResponseWriter, r *http.Request) {
	mu.Lock()
	requestCount++
	rc := requestCount
	mu.Unlock()

	logger.Info("POST /api/weather/simulate - triggering weather simulation cycle", zap.Int64("cycle", rc))

	// ~5% chance: NWS API timeout simulation
	if rand.Float64() < 0.05 {
		mu.Lock()
		errorCount++
		mu.Unlock()
		logger.Error("NWS Weather API timeout: NOAA endpoint returned 504 Gateway Timeout",
			zap.String("endpoint", "api.weather.gov/gridpoints"),
			zap.Int64("errorCount", errorCount),
		)
	}

	// ~3% chance: radar data processing error
	if rand.Float64() < 0.03 {
		mu.Lock()
		errorCount++
		mu.Unlock()
		logger.Error("NEXRAD radar data processing error: corrupt sweep data in volume scan",
			zap.String("radar", "KLOT"),
			zap.String("error", "ValueError: invalid reflectivity value at azimuth 245.3°"),
		)
		http.Error(w, `{"error":"Radar data processing failure","type":"RadarError"}`, http.StatusInternalServerError)
		return
	}

	updateAllRegions()

	// Count storm-mode regions
	stormModeRegions := 0
	totalAlerts := 0
	highRiskRegions := 0
	mu.RLock()
	for _, rw := range regionWeather {
		if rw.Forecast.StormModeActive {
			stormModeRegions++
		}
		totalAlerts += len(rw.ActiveAlerts)
		if rw.RiskScore > 50 {
			highRiskRegions++
		}
	}
	mu.RUnlock()

	logger.Info("Weather simulation cycle complete",
		zap.Int("regions", len(regions)),
		zap.Int("stormModeRegions", stormModeRegions),
		zap.Int("activeAlerts", totalAlerts),
		zap.Int("highRiskRegions", highRiskRegions),
	)

	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":           "Weather simulation cycle complete",
		"regions":          len(regions),
		"stormModeRegions": stormModeRegions,
		"activeAlerts":     totalAlerts,
		"highRiskRegions":  highRiskRegions,
	})
}

func handleCurrentConditions(w http.ResponseWriter, r *http.Request) {
	logger.Info("GET /api/weather/conditions")

	// ~4% chance: slow geolocation lookup
	if rand.Float64() < 0.04 {
		delay := 3000 + rand.Intn(4000)
		logger.Warn("Slow geolocation API response from MaxMind",
			zap.Int("delayMs", delay),
		)
		time.Sleep(time.Duration(delay) * time.Millisecond)
	}

	mu.RLock()
	defer mu.RUnlock()

	result := make(map[string]WeatherConditions)
	for name, rw := range regionWeather {
		result[name] = rw.Conditions
	}
	json.NewEncoder(w).Encode(result)
}

func handleRegionWeather(w http.ResponseWriter, r *http.Request) {
	regionName := mux.Vars(r)["region"]
	logger.Debug("GET /api/weather/region", zap.String("region", regionName))

	mu.RLock()
	rw, ok := regionWeather[regionName]
	mu.RUnlock()

	if !ok {
		http.Error(w, `{"error":"Region not found"}`, http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(rw)
}

func handleStormForecast(w http.ResponseWriter, r *http.Request) {
	logger.Info("GET /api/weather/forecast")
	mu.RLock()
	defer mu.RUnlock()

	forecasts := []StormForecast{}
	for _, rw := range regionWeather {
		forecasts = append(forecasts, rw.Forecast)
	}
	json.NewEncoder(w).Encode(forecasts)
}

func handleAlerts(w http.ResponseWriter, r *http.Request) {
	limit := 50
	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 && parsed <= 200 {
			limit = parsed
		}
	}
	logger.Info("GET /api/weather/alerts", zap.Int("limit", limit))

	mu.RLock()
	defer mu.RUnlock()

	start := 0
	if len(alerts) > limit {
		start = len(alerts) - limit
	}
	json.NewEncoder(w).Encode(alerts[start:])
}

func handleCorrelate(w http.ResponseWriter, r *http.Request) {
	var req struct {
		OutageID  string  `json:"outageId"`
		Location  string  `json:"location"`
		Latitude  float64 `json:"latitude"`
		Longitude float64 `json:"longitude"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	logger.Info("POST /api/weather/correlate",
		zap.String("outageId", req.OutageID),
		zap.String("location", req.Location),
	)

	// ~6% chance: correlation engine timeout
	if rand.Float64() < 0.06 {
		logger.Error("Weather-outage correlation engine timeout",
			zap.String("error", "context deadline exceeded after 5000ms"),
			zap.String("outageId", req.OutageID),
		)
		http.Error(w, `{"error":"Correlation engine timeout","type":"TimeoutError"}`, http.StatusGatewayTimeout)
		return
	}

	result := correlateOutageWithWeather(req.OutageID, req.Location, req.Latitude, req.Longitude)
	logger.Info("Outage-weather correlation complete",
		zap.String("outageId", req.OutageID),
		zap.Bool("weatherRelated", result.WeatherRelated),
		zap.Float64("score", result.CorrelationScore),
		zap.String("riskLevel", result.RiskLevel),
	)
	json.NewEncoder(w).Encode(result)
}

func handleCorrelationHistory(w http.ResponseWriter, r *http.Request) {
	logger.Info("GET /api/weather/correlations")
	mu.RLock()
	defer mu.RUnlock()
	json.NewEncoder(w).Encode(correlationHistory)
}

func handleSummary(w http.ResponseWriter, r *http.Request) {
	logger.Info("GET /api/weather/summary")
	mu.RLock()
	defer mu.RUnlock()

	stormModeRegions := 0
	highRiskCount := 0
	totalAlerts := len(alerts)
	avgWindSpeed := 0.0
	avgTemp := 0.0
	maxWind := 0.0
	count := 0

	for _, rw := range regionWeather {
		if rw.Forecast.StormModeActive {
			stormModeRegions++
		}
		if rw.RiskScore > 50 {
			highRiskCount++
		}
		avgWindSpeed += rw.Conditions.WindSpeed
		avgTemp += rw.Conditions.Temperature
		if rw.Conditions.WindSpeed > maxWind {
			maxWind = rw.Conditions.WindSpeed
		}
		count++
	}
	if count > 0 {
		avgWindSpeed /= float64(count)
		avgTemp /= float64(count)
	}

	weatherRelatedOutages := 0
	for _, c := range correlationHistory {
		if c.WeatherRelated {
			weatherRelatedOutages++
		}
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"regionsMonitored":     len(regions),
		"stormModeRegions":     stormModeRegions,
		"highRiskRegions":      highRiskCount,
		"activeAlerts":         totalAlerts,
		"avgWindSpeedMph":      math.Round(avgWindSpeed*10) / 10,
		"avgTemperatureF":      math.Round(avgTemp*10) / 10,
		"maxWindSpeedMph":      maxWind,
		"totalCorrelations":    len(correlationHistory),
		"weatherRelatedOutages": weatherRelatedOutages,
	})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	dbStatus := "Connected"
	if db == nil {
		dbStatus = "Disconnected"
	} else if err := db.Ping(); err != nil {
		dbStatus = "Error: " + err.Error()
	}
	rabbitStatus := "Connected"
	if rabbitCh == nil {
		rabbitStatus = "Disconnected"
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":   "Healthy",
		"service":  "WeatherCorrelationService",
		"language": "Go",
		"grpcPort": 50051,
		"httpPort": 8080,
		"database": dbStatus,
		"rabbitMQ": rabbitStatus,
		"regions":  len(regions),
	})
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// ============================================================
// Background weather updater
// ============================================================

func weatherUpdateLoop() {
	// Initial data
	updateAllRegions()
	logger.Info("Initial weather data generated for all regions")

	ticker := time.NewTicker(45 * time.Second)
	for range ticker.C {
		updateAllRegions()
	}
}

// ============================================================
// Main
// ============================================================

func main() {
	initLogger()
	defer logger.Sync()

	logger.Info("Starting Weather Correlation Service (Go)")

	connectDB()
	connectRabbitMQ()

	// Start background weather simulation
	go weatherUpdateLoop()

	// HTTP server
	r := mux.NewRouter()
	r.HandleFunc("/api/weather/simulate", handleSimulate).Methods("POST")
	r.HandleFunc("/api/weather/conditions", handleCurrentConditions).Methods("GET")
	r.HandleFunc("/api/weather/region/{region}", handleRegionWeather).Methods("GET")
	r.HandleFunc("/api/weather/forecast", handleStormForecast).Methods("GET")
	r.HandleFunc("/api/weather/alerts", handleAlerts).Methods("GET")
	r.HandleFunc("/api/weather/correlate", handleCorrelate).Methods("POST")
	r.HandleFunc("/api/weather/correlations", handleCorrelationHistory).Methods("GET")
	r.HandleFunc("/api/weather/summary", handleSummary).Methods("GET")
	r.HandleFunc("/api/weather/health", handleHealth).Methods("GET")

	// CORS + JSON content type middleware
	handler := http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		r.ServeHTTP(w, req)
	})

	httpPort := getEnv("HTTP_PORT", "8080")
	logger.Info("Weather HTTP server starting", zap.String("port", httpPort))

	// Start gRPC server in background
	go startGRPCServer()

	if err := http.ListenAndServe(":"+httpPort, handler); err != nil {
		logger.Fatal("HTTP server failed", zap.Error(err))
	}
}

func startGRPCServer() {
	grpcPort := getEnv("GRPC_PORT", "50051")
	lis, err := net.Listen("tcp", ":"+grpcPort)
	if err != nil {
		logger.Error("Failed to listen for gRPC", zap.Error(err))
		return
	}
	logger.Info("gRPC server listening", zap.String("port", grpcPort))
	// gRPC server would be registered here with proto service implementation
	// For now, the HTTP API serves all functionality
	// The gRPC listener keeps the port open for Dynatrace to detect
	for {
		conn, err := lis.Accept()
		if err != nil {
			continue
		}
		conn.Close()
	}
}
