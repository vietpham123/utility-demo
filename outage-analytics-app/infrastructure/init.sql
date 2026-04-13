-- GenericUtility Analytics Database Initialization
-- TimescaleDB (PostgreSQL with time-series extension)

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- SCHEMA: grid (Grid Topology / GIS / DMS)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS grid;

CREATE TABLE grid.substations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    capacity_mw NUMERIC(10,2) NOT NULL,
    voltage_level_kv NUMERIC(8,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Online',
    commissioned_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE grid.feeders (
    id SERIAL PRIMARY KEY,
    substation_id INT REFERENCES grid.substations(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    voltage_kv NUMERIC(8,2) NOT NULL,
    length_miles NUMERIC(8,2) NOT NULL,
    conductor_type VARCHAR(50),
    max_current_a NUMERIC(8,2),
    status VARCHAR(20) DEFAULT 'Energized',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE grid.transformers (
    id SERIAL PRIMARY KEY,
    feeder_id INT REFERENCES grid.feeders(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    capacity_kva NUMERIC(10,2) NOT NULL,
    primary_voltage_kv NUMERIC(8,2) NOT NULL,
    secondary_voltage_v NUMERIC(8,2) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    phase_config VARCHAR(10) DEFAULT '3-Phase',
    status VARCHAR(20) DEFAULT 'Online',
    install_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE grid.service_points (
    id SERIAL PRIMARY KEY,
    transformer_id INT REFERENCES grid.transformers(id),
    customer_id VARCHAR(20) NOT NULL,
    meter_id VARCHAR(20) NOT NULL,
    address VARCHAR(200),
    service_type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_service_points_customer ON grid.service_points(customer_id);
CREATE INDEX idx_service_points_meter ON grid.service_points(meter_id);
CREATE INDEX idx_service_points_transformer ON grid.service_points(transformer_id);
CREATE INDEX idx_feeders_substation ON grid.feeders(substation_id);
CREATE INDEX idx_transformers_feeder ON grid.transformers(feeder_id);

-- ============================================================
-- SCHEMA: outages (OMS)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS outages;

CREATE TABLE outages.outage_records (
    id VARCHAR(20) PRIMARY KEY,
    equipment_type VARCHAR(30),
    equipment_id INT,
    location VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    cause VARCHAR(100),
    customers_affected INT,
    priority VARCHAR(20),
    crew_assigned VARCHAR(50),
    estimated_restoration TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outage_status ON outages.outage_records(status);
CREATE INDEX idx_outage_start ON outages.outage_records(start_time DESC);

-- ============================================================
-- SCHEMA: reliability (IEEE 1366 Indices)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS reliability;

CREATE TABLE reliability.indices_daily (
    date DATE PRIMARY KEY,
    saidi NUMERIC(10,4) DEFAULT 0,
    saifi NUMERIC(10,4) DEFAULT 0,
    caidi NUMERIC(10,4) DEFAULT 0,
    maifi NUMERIC(10,4) DEFAULT 0,
    total_customers INT DEFAULT 2400000,
    total_interruptions INT DEFAULT 0,
    total_customer_minutes NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reliability.indices_monthly (
    year_month VARCHAR(7) PRIMARY KEY,
    saidi NUMERIC(10,4) DEFAULT 0,
    saifi NUMERIC(10,4) DEFAULT 0,
    caidi NUMERIC(10,4) DEFAULT 0,
    maifi NUMERIC(10,4) DEFAULT 0,
    total_customers INT DEFAULT 2400000,
    outage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SCHEMA: timeseries (TimescaleDB hypertables)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS timeseries;

-- SCADA Telemetry
CREATE TABLE timeseries.scada_readings (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(30) NOT NULL,
    equipment_type VARCHAR(30) NOT NULL,
    equipment_id INT NOT NULL,
    voltage_kv NUMERIC(10,4),
    current_a NUMERIC(10,4),
    frequency_hz NUMERIC(8,4),
    power_factor NUMERIC(5,4),
    temperature_c NUMERIC(8,2),
    active_power_kw NUMERIC(12,4),
    reactive_power_kvar NUMERIC(12,4),
    status VARCHAR(20) DEFAULT 'Normal'
);
SELECT create_hypertable('timeseries.scada_readings', 'time');
CREATE INDEX idx_scada_sensor ON timeseries.scada_readings(sensor_id, time DESC);
CREATE INDEX idx_scada_equipment ON timeseries.scada_readings(equipment_type, equipment_id, time DESC);

-- SCADA Alerts
CREATE TABLE timeseries.scada_alerts (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(30) NOT NULL,
    equipment_type VARCHAR(30) NOT NULL,
    equipment_id INT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    value NUMERIC(12,4),
    threshold NUMERIC(12,4),
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);
SELECT create_hypertable('timeseries.scada_alerts', 'time');

-- Meter Readings (AMI/MDMS)
CREATE TABLE timeseries.meter_readings (
    time TIMESTAMPTZ NOT NULL,
    meter_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    reading_kwh NUMERIC(12,4),
    demand_kw NUMERIC(10,4),
    voltage_v NUMERIC(8,2),
    current_a NUMERIC(8,4),
    power_factor NUMERIC(5,4),
    frequency_hz NUMERIC(8,4),
    quality_flag VARCHAR(20) DEFAULT 'Valid',
    validated BOOLEAN DEFAULT FALSE,
    interval_minutes INT DEFAULT 15
);
SELECT create_hypertable('timeseries.meter_readings', 'time');
CREATE INDEX idx_meter_readings_meter ON timeseries.meter_readings(meter_id, time DESC);
CREATE INDEX idx_meter_readings_customer ON timeseries.meter_readings(customer_id, time DESC);

-- Meter Anomalies
CREATE TABLE timeseries.meter_anomalies (
    time TIMESTAMPTZ NOT NULL,
    meter_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    expected_value NUMERIC(12,4),
    actual_value NUMERIC(12,4),
    message TEXT
);
SELECT create_hypertable('timeseries.meter_anomalies', 'time');

-- Demand Forecasts
CREATE TABLE timeseries.demand_forecasts (
    time TIMESTAMPTZ NOT NULL,
    area_id VARCHAR(30) NOT NULL,
    area_type VARCHAR(20) NOT NULL,
    forecast_mw NUMERIC(10,4),
    actual_mw NUMERIC(10,4),
    temperature_f NUMERIC(6,2),
    humidity_pct NUMERIC(5,2),
    confidence_low NUMERIC(10,4),
    confidence_high NUMERIC(10,4)
);
SELECT create_hypertable('timeseries.demand_forecasts', 'time');
CREATE INDEX idx_forecast_area ON timeseries.demand_forecasts(area_id, time DESC);

-- ============================================================
-- SEED: Grid Topology
-- ============================================================

-- 3 Substations
INSERT INTO grid.substations (name, code, city, state, latitude, longitude, capacity_mw, voltage_level_kv, commissioned_date) VALUES
('Lakeside Substation', 'SUB-001', 'Chicago', 'IL', 41.8781, -87.6298, 450.00, 138.00, '1998-03-15'),
('Harbor Point Substation', 'SUB-002', 'Baltimore', 'MD', 39.2904, -76.6122, 380.00, 138.00, '2002-07-22'),
('Liberty Grid Substation', 'SUB-003', 'Philadelphia', 'PA', 39.9526, -75.1652, 520.00, 230.00, '1995-11-08');

-- 12 Feeders (4 per substation)
INSERT INTO grid.feeders (substation_id, name, code, voltage_kv, length_miles, conductor_type, max_current_a) VALUES
(1, 'Lakeside Feeder North', 'FDR-001', 13.2, 8.5, 'ACSR 336.4', 600),
(1, 'Lakeside Feeder South', 'FDR-002', 13.2, 12.3, 'ACSR 336.4', 600),
(1, 'Lakeside Feeder East', 'FDR-003', 13.2, 6.7, 'ACSR 477', 800),
(1, 'Lakeside Feeder West', 'FDR-004', 4.16, 4.2, 'ACSR 4/0', 400),
(2, 'Harbor Feeder Alpha', 'FDR-005', 13.2, 9.1, 'ACSR 336.4', 600),
(2, 'Harbor Feeder Beta', 'FDR-006', 13.2, 11.8, 'ACSR 477', 800),
(2, 'Harbor Feeder Gamma', 'FDR-007', 4.16, 5.4, 'ACSR 4/0', 400),
(2, 'Harbor Feeder Delta', 'FDR-008', 13.2, 7.6, 'ACSR 336.4', 600),
(3, 'Liberty Feeder 1', 'FDR-009', 34.5, 15.2, 'ACSR 795', 1000),
(3, 'Liberty Feeder 2', 'FDR-010', 13.2, 10.4, 'ACSR 477', 800),
(3, 'Liberty Feeder 3', 'FDR-011', 13.2, 8.9, 'ACSR 336.4', 600),
(3, 'Liberty Feeder 4', 'FDR-012', 4.16, 3.8, 'ACSR 4/0', 400);

-- 36 Transformers (3 per feeder)
INSERT INTO grid.transformers (feeder_id, name, code, capacity_kva, primary_voltage_kv, secondary_voltage_v, latitude, longitude, phase_config, install_date) VALUES
-- Feeder 1 (Chicago North)
(1, 'TR-Lincoln Park', 'TRX-001', 150, 13.2, 240, 41.9214, -87.6353, '3-Phase', '2005-06-12'),
(1, 'TR-Lakeview', 'TRX-002', 75, 13.2, 120, 41.9418, -87.6536, '1-Phase', '2008-09-03'),
(1, 'TR-Uptown', 'TRX-003', 300, 13.2, 480, 41.9654, -87.6537, '3-Phase', '2001-02-18'),
-- Feeder 2 (Chicago South)
(2, 'TR-Hyde Park', 'TRX-004', 150, 13.2, 240, 41.7943, -87.5862, '3-Phase', '2010-03-22'),
(2, 'TR-Bridgeport', 'TRX-005', 112.5, 13.2, 208, 41.8383, -87.6510, '3-Phase', '2003-11-15'),
(2, 'TR-Chinatown', 'TRX-006', 75, 13.2, 120, 41.8514, -87.6355, '1-Phase', '2012-07-09'),
-- Feeder 3 (Chicago East)
(3, 'TR-Loop District', 'TRX-007', 500, 13.2, 480, 41.8823, -87.6278, '3-Phase', '1999-04-30'),
(3, 'TR-Streeterville', 'TRX-008', 225, 13.2, 208, 41.8926, -87.6187, '3-Phase', '2006-08-21'),
(3, 'TR-River North', 'TRX-009', 150, 13.2, 240, 41.8930, -87.6341, '3-Phase', '2011-01-14'),
-- Feeder 4 (Chicago West)
(4, 'TR-Wicker Park', 'TRX-010', 75, 4.16, 120, 41.9088, -87.6796, '1-Phase', '2007-05-27'),
(4, 'TR-Logan Square', 'TRX-011', 112.5, 4.16, 208, 41.9296, -87.7083, '3-Phase', '2009-12-03'),
(4, 'TR-Humboldt', 'TRX-012', 75, 4.16, 120, 41.9020, -87.7220, '1-Phase', '2015-06-18'),
-- Feeder 5 (Baltimore Alpha)
(5, 'TR-Inner Harbor', 'TRX-013', 300, 13.2, 480, 39.2860, -76.6066, '3-Phase', '2004-10-05'),
(5, 'TR-Fells Point', 'TRX-014', 150, 13.2, 240, 39.2826, -76.5903, '3-Phase', '2008-03-17'),
(5, 'TR-Canton', 'TRX-015', 112.5, 13.2, 208, 39.2802, -76.5767, '3-Phase', '2011-09-28'),
-- Feeder 6 (Baltimore Beta)
(6, 'TR-Federal Hill', 'TRX-016', 225, 13.2, 480, 39.2780, -76.6128, '3-Phase', '2002-01-20'),
(6, 'TR-Locust Point', 'TRX-017', 150, 13.2, 240, 39.2674, -76.6023, '3-Phase', '2006-04-11'),
(6, 'TR-South Baltimore', 'TRX-018', 75, 13.2, 120, 39.2711, -76.6245, '1-Phase', '2013-08-02'),
-- Feeder 7 (Baltimore Gamma)
(7, 'TR-Station North', 'TRX-019', 75, 4.16, 120, 39.3107, -76.6167, '1-Phase', '2010-11-30'),
(7, 'TR-Charles Village', 'TRX-020', 112.5, 4.16, 208, 39.3215, -76.6153, '3-Phase', '2007-02-14'),
(7, 'TR-Remington', 'TRX-021', 75, 4.16, 120, 39.3274, -76.6127, '1-Phase', '2014-05-23'),
-- Feeder 8 (Baltimore Delta)
(8, 'TR-Dundalk', 'TRX-022', 500, 13.2, 480, 39.2505, -76.5207, '3-Phase', '1997-09-08'),
(8, 'TR-Sparrows Point', 'TRX-023', 300, 13.2, 480, 39.2190, -76.4474, '3-Phase', '2000-12-19'),
(8, 'TR-Essex', 'TRX-024', 150, 13.2, 240, 39.3100, -76.4747, '3-Phase', '2005-07-06'),
-- Feeder 9 (Philadelphia Liberty 1)
(9, 'TR-Center City', 'TRX-025', 750, 34.5, 480, 39.9526, -75.1652, '3-Phase', '1996-05-14'),
(9, 'TR-University City', 'TRX-026', 500, 34.5, 480, 39.9522, -75.1932, '3-Phase', '2000-08-03'),
(9, 'TR-Spring Garden', 'TRX-027', 300, 34.5, 480, 39.9611, -75.1575, '3-Phase', '2003-02-28'),
-- Feeder 10 (Philadelphia Liberty 2)
(10, 'TR-Old City', 'TRX-028', 225, 13.2, 208, 39.9525, -75.1438, '3-Phase', '2007-10-16'),
(10, 'TR-Northern Liberties', 'TRX-029', 150, 13.2, 240, 39.9667, -75.1395, '3-Phase', '2009-06-01'),
(10, 'TR-Fishtown', 'TRX-030', 112.5, 13.2, 208, 39.9746, -75.1320, '3-Phase', '2012-12-09'),
-- Feeder 11 (Philadelphia Liberty 3)
(11, 'TR-Rittenhouse', 'TRX-031', 225, 13.2, 480, 39.9496, -75.1718, '3-Phase', '2004-04-25'),
(11, 'TR-Graduate Hospital', 'TRX-032', 150, 13.2, 240, 39.9420, -75.1760, '3-Phase', '2010-08-13'),
(11, 'TR-Point Breeze', 'TRX-033', 75, 13.2, 120, 39.9285, -75.1800, '1-Phase', '2016-01-07'),
-- Feeder 12 (Philadelphia Liberty 4)
(12, 'TR-Chestnut Hill', 'TRX-034', 112.5, 4.16, 208, 40.0710, -75.2080, '3-Phase', '2008-11-22'),
(12, 'TR-Manayunk', 'TRX-035', 75, 4.16, 120, 40.0257, -75.2260, '1-Phase', '2011-05-16'),
(12, 'TR-Roxborough', 'TRX-036', 75, 4.16, 120, 40.0390, -75.2340, '1-Phase', '2013-09-04');

-- 30 Service Points (one per customer, distributed across transformers)
INSERT INTO grid.service_points (transformer_id, customer_id, meter_id, address, service_type) VALUES
(1, 'ACCT-10001', 'MTR-20001', '1847 Oakwood Dr, Chicago, IL 60614', 'Residential'),
(7, 'ACCT-10002', 'MTR-20002', '503 Industrial Pkwy, Baltimore, MD 21201', 'Commercial'),
(28, 'ACCT-10003', 'MTR-20003', '2290 Elm Street, Philadelphia, PA 19103', 'Residential'),
(25, 'ACCT-10004', 'MTR-20004', '8100 Commerce Blvd, Washington, DC 20001', 'Industrial'),
(2, 'ACCT-10005', 'MTR-20005', '315 Shore Ave, Atlantic City, NJ 08401', 'Residential'),
(31, 'ACCT-10006', 'MTR-20006', '4422 Market St, Wilmington, DE 19801', 'Commercial'),
(3, 'ACCT-10007', 'MTR-20007', '1105 Lake Shore Dr, Chicago, IL 60611', 'Residential'),
(22, 'ACCT-10008', 'MTR-20008', '6789 Factory Rd, Baltimore, MD 21224', 'Industrial'),
(29, 'ACCT-10009', 'MTR-20009', '892 Walnut Ln, Philadelphia, PA 19147', 'Residential'),
(8, 'ACCT-10010', 'MTR-20010', '2010 Penn Ave NW, Washington, DC 20037', 'Commercial'),
(4, 'ACCT-10011', 'MTR-20011', '567 Birch Ct, Cherry Hill, NJ 08002', 'Residential'),
(13, 'ACCT-10012', 'MTR-20012', '3341 Warehouse Dist, Chicago, IL 60607', 'Commercial'),
(30, 'ACCT-10013', 'MTR-20013', '1450 Rittenhouse Sq, Philadelphia, PA 19103', 'Residential'),
(23, 'ACCT-10014', 'MTR-20014', '7800 Steel Mill Rd, Baltimore, MD 21230', 'Industrial'),
(14, 'ACCT-10015', 'MTR-20015', '224 Boardwalk, Atlantic City, NJ 08401', 'Commercial'),
(5, 'ACCT-10016', 'MTR-20016', '9012 Georgetown Rd, Washington, DC 20007', 'Residential'),
(10, 'ACCT-10017', 'MTR-20017', '1780 Wicker Park, Chicago, IL 60622', 'Residential'),
(15, 'ACCT-10018', 'MTR-20018', '450 Brandywine Blvd, Wilmington, DE 19802', 'Commercial'),
(16, 'ACCT-10019', 'MTR-20019', '3025 Canton St, Baltimore, MD 21224', 'Residential'),
(26, 'ACCT-10020', 'MTR-20020', '5567 Spring Garden, Philadelphia, PA 19123', 'Industrial'),
(6, 'ACCT-10021', 'MTR-20021', '188 Dupont Circle, Washington, DC 20036', 'Residential'),
(9, 'ACCT-10022', 'MTR-20022', '6320 Navy Pier Dr, Chicago, IL 60611', 'Commercial'),
(32, 'ACCT-10023', 'MTR-20023', '741 Margate Ave, Ventnor City, NJ 08406', 'Residential'),
(17, 'ACCT-10024', 'MTR-20024', '2100 N Charles St, Baltimore, MD 21218', 'Residential'),
(33, 'ACCT-10025', 'MTR-20025', '980 Chestnut Hill, Philadelphia, PA 19118', 'Residential'),
(11, 'ACCT-10026', 'MTR-20026', '4455 H Street NE, Washington, DC 20002', 'Commercial'),
(12, 'ACCT-10027', 'MTR-20027', '1330 Logan Sq, Chicago, IL 60607', 'Residential'),
(24, 'ACCT-10028', 'MTR-20028', '705 Kirkwood Hwy, Wilmington, DE 19805', 'Industrial'),
(18, 'ACCT-10029', 'MTR-20029', '2678 Federal Hill, Baltimore, MD 21230', 'Residential'),
(27, 'ACCT-10030', 'MTR-20030', '5100 Plant Rd, Chester, PA 19013', 'Industrial');

-- ============================================================
-- SEED: Reliability baseline (last 30 days)
-- ============================================================
-- IEEE 1366 realistic daily indices for a ~2.4M customer utility
-- Annual benchmarks: SAIDI ~120-200 min, SAIFI ~1.0-1.3, CAIDI ~90-140 min, MAIFI ~4-8
-- Daily values = annual / 365, with variance for weather events
INSERT INTO reliability.indices_daily (date, saidi, saifi, caidi, maifi, total_customers, total_interruptions, total_customer_minutes)
SELECT 
    d::date,
    ROUND((0.15 + random() * 0.65)::numeric, 4) as saidi,       -- daily: 0.15-0.80 min/cust (annual ~55-290)
    ROUND((0.001 + random() * 0.006)::numeric, 4) as saifi,     -- daily: 0.001-0.007 (annual ~0.4-2.6)
    ROUND((70 + random() * 90)::numeric, 4) as caidi,           -- 70-160 min per interruption
    ROUND((0.005 + random() * 0.03)::numeric, 4) as maifi,      -- daily: 0.005-0.035 (annual ~1.8-12.8)
    2400000,                                                      -- 2.4M customers served
    floor(2 + random() * 8)::int,                                 -- 2-9 interruptions/day
    ROUND((360000 + random() * 1560000)::numeric, 2)              -- 360K-1.92M customer-minutes/day
FROM generate_series(NOW() - INTERVAL '30 days', NOW() - INTERVAL '1 day', '1 day') AS d;

GRANT ALL ON ALL TABLES IN SCHEMA grid TO utilityuser;
GRANT ALL ON ALL TABLES IN SCHEMA outages TO utilityuser;
GRANT ALL ON ALL TABLES IN SCHEMA reliability TO utilityuser;
GRANT ALL ON ALL TABLES IN SCHEMA timeseries TO utilityuser;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA grid TO utilityuser;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA outages TO utilityuser;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA reliability TO utilityuser;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA timeseries TO utilityuser;
GRANT USAGE ON SCHEMA grid TO utilityuser;
GRANT USAGE ON SCHEMA outages TO utilityuser;
GRANT USAGE ON SCHEMA reliability TO utilityuser;
GRANT USAGE ON SCHEMA timeseries TO utilityuser;
