package com.genericutility.meterdata.controller;

import com.genericutility.meterdata.service.MeterSimulatorService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api/meter-data")
public class MeterDataController {

    private static final Logger log = LoggerFactory.getLogger(MeterDataController.class);
    private int requestCount = 0;

    @Autowired
    private MeterSimulatorService simulator;

    @Autowired
    private RestTemplate restTemplate;

    @Value("${grid.topology.service.url:http://grid-topology-service:3000}")
    private String gridTopologyServiceUrl;

    @GetMapping("/readings")
    public Object getReadings(
            @RequestParam(required = false) String meterId,
            @RequestParam(defaultValue = "100") int limit) {
        requestCount++;
        log.debug("GET /api/meter-data/readings - request #{}, meterId={}, limit={}", requestCount, meterId, limit);

        // ~3% chance: simulate slow query with large result set
        if (ThreadLocalRandom.current().nextDouble() < 0.03) {
            try {
                long delay = 3000 + ThreadLocalRandom.current().nextLong(4000);
                log.warn("Slow meter readings query detected - simulating delay of {}ms for request #{}", delay, requestCount);
                Thread.sleep(delay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        int safeLimit = Math.min(limit, 500);
        List<Map<String, Object>> readings = simulator.getRecentReadings();
        if (meterId != null && !meterId.isEmpty()) {
            readings = readings.stream()
                .filter(r -> meterId.equals(r.get("meterId")))
                .collect(Collectors.toList());
        }
        int start = Math.max(0, readings.size() - safeLimit);
        List<Map<String, Object>> result = readings.subList(start, readings.size());
        Collections.reverse(result);
        log.info("GET /api/meter-data/readings meterId={} count={}", meterId, result.size());
        return result;
    }

    @GetMapping("/readings/{meterId}")
    public List<Map<String, Object>> getReadingsByMeter(
            @PathVariable String meterId,
            @RequestParam(defaultValue = "50") int limit) {
        int safeLimit = Math.min(limit, 200);
        List<Map<String, Object>> readings = simulator.getRecentReadings().stream()
            .filter(r -> meterId.equals(r.get("meterId")))
            .collect(Collectors.toList());
        int start = Math.max(0, readings.size() - safeLimit);
        List<Map<String, Object>> result = new ArrayList<>(readings.subList(start, readings.size()));
        Collections.reverse(result);
        return result;
    }

    @GetMapping("/readings/customer/{customerId}")
    public List<Map<String, Object>> getReadingsByCustomer(@PathVariable String customerId) {
        return simulator.getRecentReadings().stream()
            .filter(r -> customerId.equals(r.get("customerId")))
            .collect(Collectors.toList());
    }

    @GetMapping("/anomalies")
    public List<Map<String, Object>> getAnomalies(@RequestParam(defaultValue = "50") int limit) {
        List<Map<String, Object>> anomalies = simulator.getRecentAnomalies();
        int safeLimit = Math.min(limit, 200);
        int start = Math.max(0, anomalies.size() - safeLimit);
        List<Map<String, Object>> result = new ArrayList<>(anomalies.subList(start, anomalies.size()));
        Collections.reverse(result);
        log.info("GET /api/meter-data/anomalies count={}", result.size());
        return result;
    }

    @GetMapping("/meters")
    public List<Map<String, String>> getMeters() {
        return simulator.getMeterProfiles().values().stream()
            .map(p -> {
                Map<String, String> m = new LinkedHashMap<>();
                m.put("meterId", p.meterId);
                m.put("customerId", p.customerId);
                m.put("serviceType", p.serviceType);
                return m;
            })
            .collect(Collectors.toList());
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        List<Map<String, Object>> readings = simulator.getRecentReadings();
        double totalKwh = readings.stream()
            .mapToDouble(r -> ((Number)r.get("readingKwh")).doubleValue()).sum();
        long validatedCount = readings.stream()
            .filter(r -> Boolean.TRUE.equals(r.get("validated"))).count();
        long suspectCount = readings.stream()
            .filter(r -> "Suspect".equals(r.get("qualityFlag"))).count();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("totalReadings", readings.size());
        summary.put("totalKwh", Math.round(totalKwh * 100.0) / 100.0);
        summary.put("validatedCount", validatedCount);
        summary.put("suspectCount", suspectCount);
        summary.put("anomalyCount", simulator.getRecentAnomalies().size());
        summary.put("meterCount", simulator.getMeterProfiles().size());
        summary.put("avgKwhPerReading", readings.isEmpty() ? 0 :
            Math.round(totalKwh / readings.size() * 100.0) / 100.0);
        log.info("GET /api/meter-data/summary");
        return summary;
    }

    @PostMapping("/simulate")
    public Object simulate() {
        log.info("POST /api/meter-data/simulate - triggering simulation cycle");

        // Fetch grid topology stats for meter location validation (adds PurePath depth)
        try {
            String gridStatsUrl = gridTopologyServiceUrl + "/api/grid/stats";
            @SuppressWarnings("unchecked")
            Map<String, Object> gridStats = restTemplate.getForObject(gridStatsUrl, Map.class);
            if (gridStats != null) {
                log.info("Fetched grid topology stats for meter validation: substations={}", gridStats.get("substations"));
            }
        } catch (Exception e) {
            log.warn("Grid-topology-service enrichment failed (non-critical): {}", e.getMessage());
        }

        // ~5% chance: simulate VEE pipeline failure
        if (ThreadLocalRandom.current().nextDouble() < 0.05) {
            log.error("VEE pipeline validation failure - meter data integrity check failed. " +
                    "Affected meters: MTR-{}, MTR-{}. Cause: checksum mismatch in reading batch",
                    20000 + ThreadLocalRandom.current().nextInt(30),
                    20000 + ThreadLocalRandom.current().nextInt(30));
            Map<String, Object> error = new LinkedHashMap<>();
            error.put("error", "VEE pipeline validation failure - batch rejected");
            error.put("type", "DataIntegrityError");
            throw new RuntimeException("VEE pipeline validation failure - meter data integrity check failed");
        }

        try {
            simulator.simulateReadings();
        } catch (RuntimeException e) {
            log.error("Simulation cycle failed: {}", e.getMessage(), e);
            throw e;
        }

        log.debug("Simulate complete: readings={}, anomalies={}, meters={}",
                simulator.getRecentReadings().size(), simulator.getRecentAnomalies().size(), simulator.getMeterProfiles().size());

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", "Simulation cycle complete");
        result.put("totalReadings", simulator.getRecentReadings().size());
        result.put("anomalyCount", simulator.getRecentAnomalies().size());
        result.put("meterCount", simulator.getMeterProfiles().size());
        return result;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        Map<String, Object> h = new LinkedHashMap<>();
        h.put("status", "Healthy");
        h.put("service", "MeterDataService");
        h.put("readings", simulator.getRecentReadings().size());
        h.put("meters", simulator.getMeterProfiles().size());
        return h;
    }
}
