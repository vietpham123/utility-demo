package com.genericutility.meterdata.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

@Service
public class MeterSimulatorService {

    private static final Logger log = LoggerFactory.getLogger(MeterSimulatorService.class);
    private static final int TOTAL_METERS = 30;
    private static final ObjectMapper mapper = new ObjectMapper();

    private final ConcurrentLinkedDeque<Map<String, Object>> recentReadings = new ConcurrentLinkedDeque<>();
    private final ConcurrentLinkedDeque<Map<String, Object>> recentAnomalies = new ConcurrentLinkedDeque<>();
    private final Map<String, MeterProfile> meterProfiles = new LinkedHashMap<>();
    private int batchCount = 0;
    private int errorCount = 0;

    @Autowired private JdbcTemplate jdbc;
    @Autowired(required = false) private KafkaTemplate<String, String> kafka;
    @Autowired(required = false) private StringRedisTemplate redis;

    public static class MeterProfile {
        public String meterId, customerId, serviceType;
        public double baseUsageKwh, baseVoltageV;
        MeterProfile(int idx) {
            this.meterId = "MTR-" + (20000 + idx);
            this.customerId = "ACCT-" + (10000 + idx);
            int[] commercial = {2,6,10,12,15,18,22,26};
            int[] industrial = {4,8,14,20,28,30};
            boolean isCommercial = Arrays.stream(commercial).anyMatch(c -> c == idx);
            boolean isIndustrial = Arrays.stream(industrial).anyMatch(c -> c == idx);
            this.serviceType = isIndustrial ? "Industrial" : isCommercial ? "Commercial" : "Residential";
            this.baseUsageKwh = isIndustrial ? 450 : isCommercial ? 110 : 25;
            this.baseVoltageV = isIndustrial ? 480 : 240;
        }
    }

    @PostConstruct
    public void init() {
        for (int i = 1; i <= TOTAL_METERS; i++) {
            MeterProfile p = new MeterProfile(i);
            meterProfiles.put(p.meterId, p);
        }
        log.info("Initialized {} meter profiles", meterProfiles.size());

        // Seed 24 hours of historical readings (one per meter per hour)
        try {
            Instant now = Instant.now();
            for (int hoursAgo = 24; hoursAgo >= 1; hoursAgo--) {
                Instant ts = now.minus(hoursAgo, ChronoUnit.HOURS);
                for (MeterProfile p : meterProfiles.values()) {
                    Map<String, Object> reading = generateReading(p, ts);
                    persistReading(reading);
                    recentReadings.addLast(reading);
                }
            }
            trimReadings();
            log.info("Seeded {} historical readings", recentReadings.size());
        } catch (Exception e) {
            log.warn("Error seeding historical data: {}", e.getMessage());
        }
    }

    @Scheduled(fixedDelayString = "${meter.interval:20000}", initialDelay = 30000)
    public void simulateReadings() {
        batchCount++;
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        Instant now = Instant.now();

        log.debug("Starting meter batch #{}, totalReadings={}", batchCount, recentReadings.size());

        // ~7% chance: simulate HikariCP connection pool exhaustion
        if (rng.nextDouble() < 0.07) {
            errorCount++;
            log.error("HikariCP connection pool exhausted - cannot acquire connection within 30000ms. " +
                    "Pool stats: total=10, active=10, idle=0, waiting=3. Batch #{}, totalErrors={}",
                    batchCount, errorCount);
            throw new RuntimeException("HikariCP - Connection is not available, request timed out after 30000ms");
        }

        // ~5% chance: simulate Kafka broker unreachable
        if (rng.nextDouble() < 0.05) {
            errorCount++;
            log.error("Kafka broker unreachable during meter reading publish - broker={}, topic=meter.readings.validated, batch={}",
                    System.getenv("KAFKA_BROKER") != null ? System.getenv("KAFKA_BROKER") : "kafka:9092", batchCount);
        }

        // Generate readings for a batch of random meters (5-10 per cycle)
        int batchSize = 5 + rng.nextInt(6);
        List<MeterProfile> batch = new ArrayList<>(meterProfiles.values());
        Collections.shuffle(batch);
        batch = batch.subList(0, Math.min(batchSize, batch.size()));

        for (MeterProfile meter : batch) {
            try {
                Map<String, Object> reading = generateReading(meter, now);

                // VEE: Validation, Estimation, Editing
                reading = validateReading(reading, meter);

                recentReadings.addLast(reading);
                persistReading(reading);
                publishReading(reading);
                cacheReading(reading);
            } catch (Exception e) {
                log.error("Error generating reading for {}: {}", meter.meterId, e.getMessage());
            }
        }

        trimReadings();
        log.info("Meter batch #{}: {} readings generated, anomalies={}", batchCount, batchSize, recentAnomalies.size());
        log.debug("Batch details: readingsInMemory={}, anomaliesInMemory={}", recentReadings.size(), recentAnomalies.size());
    }

    private Map<String, Object> generateReading(MeterProfile meter, Instant timestamp) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        int hour = java.time.ZonedDateTime.ofInstant(timestamp, java.time.ZoneId.systemDefault()).getHour();
        boolean isPeak = hour >= 8 && hour <= 20;
        double seasonFactor = 1.0 + 0.3 * Math.sin((java.time.LocalDate.now().getMonthValue() - 1) * Math.PI / 6);
        double timeFactor = isPeak ? (1.0 + 0.5 * Math.sin((hour - 8) * Math.PI / 12)) : 0.5;
        double noise = 0.9 + rng.nextDouble() * 0.2;

        double kwh = Math.round(meter.baseUsageKwh * seasonFactor * timeFactor * noise * 100.0) / 100.0;
        double demandKw = Math.round(kwh * (0.1 + rng.nextDouble() * 0.1) * 100.0) / 100.0;
        double voltageV = Math.round((meter.baseVoltageV * (0.95 + rng.nextDouble() * 0.10)) * 100.0) / 100.0;
        double currentA = Math.round((kwh / voltageV * 1000 * (0.8 + rng.nextDouble() * 0.2)) * 100.0) / 100.0;
        double pf = Math.round((0.85 + rng.nextDouble() * 0.14) * 10000.0) / 10000.0;
        double freq = Math.round((59.95 + rng.nextDouble() * 0.1) * 10000.0) / 10000.0;

        Map<String, Object> reading = new LinkedHashMap<>();
        reading.put("time", timestamp.toString());
        reading.put("meterId", meter.meterId);
        reading.put("customerId", meter.customerId);
        reading.put("readingKwh", kwh);
        reading.put("demandKw", demandKw);
        reading.put("voltageV", voltageV);
        reading.put("currentA", currentA);
        reading.put("powerFactor", pf);
        reading.put("frequencyHz", freq);
        reading.put("qualityFlag", "Valid");
        reading.put("validated", false);
        reading.put("intervalMinutes", 15);
        return reading;
    }

    private Map<String, Object> validateReading(Map<String, Object> reading, MeterProfile meter) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        double kwh = ((Number) reading.get("readingKwh")).doubleValue();
        double voltageV = ((Number) reading.get("voltageV")).doubleValue();

        // VEE Check 1: Usage within expected bounds
        if (kwh > meter.baseUsageKwh * 3) {
            reading.put("qualityFlag", "Estimated");
            reading.put("readingKwh", Math.round(meter.baseUsageKwh * 1.2 * 100.0) / 100.0);
            reportAnomaly(reading, "Excessive Usage", "Medium",
                meter.baseUsageKwh * 3, kwh, "Reading exceeds 3x baseline, estimated");
        }

        // VEE Check 2: Voltage in bounds
        if (voltageV < meter.baseVoltageV * 0.88 || voltageV > meter.baseVoltageV * 1.10) {
            reading.put("qualityFlag", "Suspect");
            reportAnomaly(reading, "Voltage Out of Range", "High",
                meter.baseVoltageV, voltageV, "Meter voltage outside ANSI C84.1 Range A");
        }

        // ~2% chance of random anomaly detection (potential tamper, meter malfunction)
        if (rng.nextDouble() < 0.02) {
            String[] anomalyTypes = {"Potential Tamper", "Meter Communication Loss", "Reverse Power Flow", "Zero Usage Alert"};
            String type = anomalyTypes[rng.nextInt(anomalyTypes.length)];
            reading.put("qualityFlag", "Suspect");
            reportAnomaly(reading, type, "High", 0, 0,
                type + " detected for " + meter.meterId);
        }

        reading.put("validated", true);
        return reading;
    }

    private void reportAnomaly(Map<String, Object> reading, String type, String severity,
                               double expected, double actual, String message) {
        Map<String, Object> anomaly = new LinkedHashMap<>();
        anomaly.put("time", reading.get("time"));
        anomaly.put("meterId", reading.get("meterId"));
        anomaly.put("customerId", reading.get("customerId"));
        anomaly.put("anomalyType", type);
        anomaly.put("severity", severity);
        anomaly.put("expectedValue", expected);
        anomaly.put("actualValue", actual);
        anomaly.put("message", message);
        recentAnomalies.addLast(anomaly);
        while (recentAnomalies.size() > 200) recentAnomalies.pollFirst();

        // Persist and publish anomaly
        try {
            jdbc.update("INSERT INTO timeseries.meter_anomalies (time,meter_id,customer_id,anomaly_type,severity,expected_value,actual_value,message) VALUES (?::timestamptz,?,?,?,?,?,?,?)",
                anomaly.get("time").toString(), anomaly.get("meterId"), anomaly.get("customerId"),
                type, severity, expected, actual, message);
        } catch (Exception e) { log.warn("DB anomaly persist error: {}", e.getMessage()); }

        try {
            if (kafka != null) kafka.send("meter.anomalies", (String)anomaly.get("meterId"), mapper.writeValueAsString(anomaly));
        } catch (Exception e) { log.warn("Kafka anomaly publish error: {}", e.getMessage()); }

        log.warn("ANOMALY: {} - {} for {}", type, message, reading.get("meterId"));
    }

    private void persistReading(Map<String, Object> r) {
        try {
            jdbc.update("INSERT INTO timeseries.meter_readings (time,meter_id,customer_id,reading_kwh,demand_kw,voltage_v,current_a,power_factor,frequency_hz,quality_flag,validated,interval_minutes) VALUES (?::timestamptz,?,?,?,?,?,?,?,?,?,?,?)",
                r.get("time").toString(), r.get("meterId"), r.get("customerId"),
                r.get("readingKwh"), r.get("demandKw"), r.get("voltageV"), r.get("currentA"),
                r.get("powerFactor"), r.get("frequencyHz"), r.get("qualityFlag"),
                r.get("validated"), r.get("intervalMinutes"));
        } catch (Exception e) { log.warn("DB persist error: {}", e.getMessage()); }
    }

    private void publishReading(Map<String, Object> r) {
        try {
            if (kafka != null) kafka.send("meter.readings.validated", (String)r.get("meterId"), mapper.writeValueAsString(r));
        } catch (Exception e) { log.warn("Kafka publish error: {}", e.getMessage()); }
    }

    private void cacheReading(Map<String, Object> r) {
        try {
            if (redis != null) {
                redis.opsForValue().set("meter:latest:" + r.get("meterId"), mapper.writeValueAsString(r), 5, TimeUnit.MINUTES);
            }
        } catch (Exception e) { /* ignore */ }
    }

    private void trimReadings() {
        while (recentReadings.size() > 2000) recentReadings.pollFirst();
    }

    public List<Map<String, Object>> getRecentReadings() { return new ArrayList<>(recentReadings); }
    public List<Map<String, Object>> getRecentAnomalies() { return new ArrayList<>(recentAnomalies); }
    public Map<String, MeterProfile> getMeterProfiles() { return meterProfiles; }
}
