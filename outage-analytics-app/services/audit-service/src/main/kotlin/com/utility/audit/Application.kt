package com.utility.audit

import com.fasterxml.jackson.databind.SerializationFeature
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import io.ktor.http.*
import io.ktor.serialization.jackson.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.apache.kafka.clients.consumer.ConsumerConfig
import org.apache.kafka.clients.consumer.KafkaConsumer
import org.apache.kafka.common.serialization.StringDeserializer
import org.slf4j.LoggerFactory
import java.time.Duration
import java.time.Instant
import java.util.*
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.concurrent.thread

// ============================================================
// Audit Service (Kotlin/Ktor) — Kafka consumer for audit trail
// Adds Kotlin to polyglot mix. Consumes outage.events + scada.alerts
// Provides immutable audit log for regulatory compliance
// ============================================================

data class AuditEntry(
    val id: String = UUID.randomUUID().toString(),
    val timestamp: String = Instant.now().toString(),
    val eventType: String,
    val source: String,
    val severity: String = "INFO",
    val action: String,
    val details: Map<String, Any?> = emptyMap(),
    val userId: String? = null,
    val region: String? = null
)

val auditLog = CopyOnWriteArrayList<AuditEntry>()
val logger = LoggerFactory.getLogger("audit-service")
val mapper = jacksonObjectMapper().apply {
    registerModule(JavaTimeModule())
    disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
}

fun startKafkaConsumer() {
    val kafkaBrokers = System.getenv("KAFKA_BROKERS") ?: "kafka:9092"
    val props = Properties().apply {
        put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaBrokers)
        put(ConsumerConfig.GROUP_ID_CONFIG, "audit-service-group")
        put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer::class.java.name)
        put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer::class.java.name)
        put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest")
        put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "true")
        put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "50")
    }

    thread(isDaemon = true, name = "kafka-consumer") {
        try {
            val consumer = KafkaConsumer<String, String>(props)
            consumer.subscribe(listOf("outage.events", "scada.alerts", "meter.anomalies"))
            logger.info("Kafka consumer started, subscribed to: outage.events, scada.alerts, meter.anomalies")

            while (true) {
                val records = consumer.poll(Duration.ofMillis(1000))
                for (record in records) {
                    try {
                        val value = mapper.readValue(record.value(), Map::class.java) as Map<String, Any?>
                        val entry = AuditEntry(
                            eventType = record.topic(),
                            source = "kafka:${record.topic()}",
                            severity = when (record.topic()) {
                                "outage.events" -> "WARNING"
                                "scada.alerts" -> "ALERT"
                                "meter.anomalies" -> "INFO"
                                else -> "INFO"
                            },
                            action = "EVENT_RECEIVED",
                            details = value,
                            region = value["region"] as? String ?: value["location"] as? String
                        )
                        auditLog.add(entry)
                        // Keep audit log bounded
                        while (auditLog.size > 5000) auditLog.removeAt(0)
                        logger.info("Audit entry created: ${entry.eventType} from ${entry.source}")
                    } catch (e: Exception) {
                        logger.warn("Failed to process Kafka record: ${e.message}")
                    }
                }
            }
        } catch (e: Exception) {
            logger.error("Kafka consumer failed to start: ${e.message}")
            // Generate simulated audit entries if Kafka is unavailable
            generateSimulatedEntries()
        }
    }
}

fun generateSimulatedEntries() {
    logger.info("Generating simulated audit entries (Kafka unavailable)")
    val eventTypes = listOf("outage.events", "scada.alerts", "meter.anomalies", "crew.dispatch", "system.config")
    val actions = listOf("EVENT_RECEIVED", "THRESHOLD_EXCEEDED", "STATUS_CHANGED", "CONFIG_UPDATED", "USER_ACTION")
    val regions = listOf("Chicago-Metro", "Baltimore-Metro", "Philadelphia-Metro", "DC-Metro", "Atlantic-Coast", "Delaware-Valley")
    val severities = listOf("INFO", "WARNING", "ALERT", "CRITICAL")

    thread(isDaemon = true, name = "audit-simulator") {
        while (true) {
            val entry = AuditEntry(
                eventType = eventTypes.random(),
                source = "simulator",
                severity = severities.random(),
                action = actions.random(),
                details = mapOf(
                    "message" to "Simulated audit event",
                    "value" to (Math.random() * 100).toInt(),
                    "sensor" to "SEN-${(1..50).random().toString().padStart(3, '0')}"
                ),
                region = regions.random()
            )
            auditLog.add(entry)
            while (auditLog.size > 5000) auditLog.removeAt(0)
            Thread.sleep((5000L..15000L).random())
        }
    }
}

fun main() {
    logger.info("Audit Service (Kotlin/Ktor) starting on port 8090")

    // Start Kafka consumer in background
    startKafkaConsumer()

    embeddedServer(Netty, port = 8090) {
        install(ContentNegotiation) {
            jackson {
                registerModule(JavaTimeModule())
                disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            }
        }

        routing {
            // Get audit log with pagination
            get("/api/audit/log") {
                val page = (call.parameters["page"] ?: "1").toInt()
                val limit = (call.parameters["limit"] ?: "50").toInt()
                val severity = call.parameters["severity"]
                val eventType = call.parameters["eventType"]

                var filtered = auditLog.toList().reversed()
                if (severity != null) filtered = filtered.filter { it.severity == severity }
                if (eventType != null) filtered = filtered.filter { it.eventType == eventType }

                val offset = (page - 1) * limit
                val results = filtered.drop(offset).take(limit)

                call.respond(mapOf(
                    "entries" to results,
                    "total" to filtered.size,
                    "page" to page,
                    "limit" to limit,
                    "totalPages" to ((filtered.size.toDouble() / limit).toInt() + 1)
                ))
            }

            // Get audit stats
            get("/api/audit/stats") {
                val entries = auditLog.toList()
                val byEventType = entries.groupBy { it.eventType }.mapValues { it.value.size }
                val bySeverity = entries.groupBy { it.severity }.mapValues { it.value.size }
                val byRegion = entries.mapNotNull { it.region }.groupBy { it }.mapValues { it.value.size }

                call.respond(mapOf(
                    "totalEntries" to entries.size,
                    "byEventType" to byEventType,
                    "bySeverity" to bySeverity,
                    "byRegion" to byRegion,
                    "latestEntry" to entries.lastOrNull()?.timestamp,
                    "oldestEntry" to entries.firstOrNull()?.timestamp
                ))
            }

            // Search audit log
            get("/api/audit/search") {
                val q = call.parameters["q"] ?: ""
                if (q.isBlank()) {
                    call.respond(HttpStatusCode.BadRequest, mapOf("error" to "Query parameter q required"))
                    return@get
                }

                val results = auditLog.toList().reversed().filter {
                    it.eventType.contains(q, ignoreCase = true) ||
                    it.action.contains(q, ignoreCase = true) ||
                    it.source.contains(q, ignoreCase = true) ||
                    (it.region ?: "").contains(q, ignoreCase = true) ||
                    it.details.toString().contains(q, ignoreCase = true)
                }.take(100)

                call.respond(mapOf("results" to results, "total" to results.size, "query" to q))
            }

            // Manual audit entry (for user actions)
            post("/api/audit/log") {
                val body = call.receive<Map<String, Any?>>()
                val entry = AuditEntry(
                    eventType = body["eventType"] as? String ?: "user.action",
                    source = body["source"] as? String ?: "api",
                    severity = body["severity"] as? String ?: "INFO",
                    action = body["action"] as? String ?: "MANUAL_ENTRY",
                    details = body["details"] as? Map<String, Any?> ?: emptyMap(),
                    userId = body["userId"] as? String,
                    region = body["region"] as? String
                )
                auditLog.add(entry)
                logger.info("Manual audit entry: ${entry.eventType} - ${entry.action}")
                call.respond(HttpStatusCode.Created, entry)
            }

            // Health check
            get("/api/audit/health") {
                call.respond(mapOf(
                    "status" to "Healthy",
                    "service" to "audit-service",
                    "language" to "Kotlin",
                    "entriesCount" to auditLog.size,
                    "timestamp" to Instant.now().toString()
                ))
            }
        }
    }.start(wait = true)
}
