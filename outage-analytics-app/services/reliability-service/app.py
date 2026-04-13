import os, json, time, math, logging, threading, random, traceback
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer, KafkaProducer

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
log = logging.getLogger('reliability-service')

# Counters for error tracking
calculation_count = 0
error_count = 0

import urllib.parse as _urlparse
_db_url = os.getenv('DATABASE_URL', '')
if _db_url:
    _p = _urlparse.urlparse(_db_url)
    DB_CONFIG = {
        'host': _p.hostname or os.getenv('DB_HOST', 'timescaledb'),
        'port': _p.port or int(os.getenv('DB_PORT', '5432')),
        'dbname': (_p.path or '').lstrip('/') or os.getenv('DB_NAME', 'utilitydb'),
        'user': _p.username or os.getenv('DB_USER', 'utilityuser'),
        'password': _p.password or os.getenv('DB_PASSWORD', '')
    }
else:
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'timescaledb'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'dbname': os.getenv('DB_NAME', 'utilitydb'),
        'user': os.getenv('DB_USER', 'utilityuser'),
        'password': os.getenv('DB_PASSWORD', '')
    }
KAFKA_BROKER = os.getenv('KAFKA_BROKERS', os.getenv('KAFKA_BROKER', 'kafka:9092'))
TOTAL_CUSTOMERS = 2_400_000  # ~2.4M customers served across 17 service territory states

# In-memory state
current_indices = {
    'saidi': 0.0, 'saifi': 0.0, 'caidi': 0.0, 'maifi': 0.0,
    'total_customers': TOTAL_CUSTOMERS,
    'total_interruptions_today': 0,
    'total_customer_minutes_today': 0.0,
    'last_calculated': None
}
recent_events = []

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def calculate_indices():
    """Recalculate IEEE 1366 reliability indices from outage data."""
    global calculation_count, error_count
    calculation_count += 1
    log.debug(f"Starting reliability calculation #{calculation_count}")

    # ~8% chance: simulate database connection error
    if random.random() < 0.08:
        error_count += 1
        log.error(f"PostgreSQL connection failed: could not connect to server: Connection refused. "
                  f"Is the server running on host 'timescaledb' and accepting TCP/IP connections on port 5432? "
                  f"Calculation #{calculation_count}, totalErrors={error_count}")
        raise ConnectionError("Database connection refused during reliability calculation")

    # ~4% chance: simulate slow query warning
    if random.random() < 0.04:
        log.warning(f"Slow outage query detected - sequential scan on outages.outage_records. "
                    f"Consider running ANALYZE or adding index on start_time. Calculation #{calculation_count}")

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log.debug("Database connection acquired for reliability calculation")

        today = datetime.now(timezone.utc).date()

        # Get today's outage data
        cur.execute("""
            SELECT id, customers_affected, start_time, end_time, status
            FROM outages.outage_records
            WHERE start_time::date = %s OR (start_time::date < %s AND (end_time IS NULL OR end_time::date >= %s))
        """, (today, today, today))
        outages = cur.fetchall()

        log.debug(f"Found {len(outages)} outage records for today's calculation")

        total_customer_interruptions = 0
        total_customer_minutes = 0.0
        momentary_interruptions = 0

        for outage in outages:
            affected = outage.get('customers_affected', 0) or 0
            start = outage['start_time']
            end = outage.get('end_time')

            if end:
                duration_minutes = (end - start).total_seconds() / 60
            else:
                duration_minutes = (datetime.now(timezone.utc) - start.replace(tzinfo=timezone.utc) if start.tzinfo is None else datetime.now(timezone.utc) - start).total_seconds() / 60

            if duration_minutes < 5:
                momentary_interruptions += 1
            else:
                total_customer_interruptions += affected
                total_customer_minutes += affected * duration_minutes

        # IEEE 1366 Indices:
        # SAIDI = Sum(Customer Interruption Durations) / Total Customers
        # SAIFI = Total Customer Interruptions / Total Customers
        # CAIDI = SAIDI / SAIFI (average restoration time per interruption)
        # MAIFI = Momentary Interruptions / Total Customers
        saidi = round(total_customer_minutes / TOTAL_CUSTOMERS, 4) if TOTAL_CUSTOMERS > 0 else 0
        saifi = round(total_customer_interruptions / TOTAL_CUSTOMERS, 4) if TOTAL_CUSTOMERS > 0 else 0
        caidi = round(total_customer_minutes / total_customer_interruptions, 4) if total_customer_interruptions > 0 else 0
        maifi = round(momentary_interruptions / TOTAL_CUSTOMERS, 4) if TOTAL_CUSTOMERS > 0 else 0

        current_indices.update({
            'saidi': saidi, 'saifi': saifi, 'caidi': caidi, 'maifi': maifi,
            'total_interruptions_today': len(outages),
            'total_customer_minutes_today': round(total_customer_minutes, 2),
            'last_calculated': datetime.now(timezone.utc).isoformat()
        })

        # Persist daily calculation
        cur.execute("""
            INSERT INTO reliability.indices_daily (date, saidi, saifi, caidi, maifi, total_customers, total_interruptions, total_customer_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                saidi = EXCLUDED.saidi, saifi = EXCLUDED.saifi,
                caidi = EXCLUDED.caidi, maifi = EXCLUDED.maifi,
                total_interruptions = EXCLUDED.total_interruptions,
                total_customer_minutes = EXCLUDED.total_customer_minutes
        """, (today, saidi, saifi, caidi, maifi, TOTAL_CUSTOMERS, len(outages), round(total_customer_minutes, 2)))
        conn.commit()
        cur.close()
        conn.close()

        log.info(f"Indices calculated #{calculation_count}: SAIDI={saidi} SAIFI={saifi} CAIDI={caidi} MAIFI={maifi}")
        log.debug(f"Calculation details: customerInterruptions={total_customer_interruptions}, "
                  f"customerMinutes={round(total_customer_minutes, 2)}, momentaryInterruptions={momentary_interruptions}, "
                  f"outagesProcessed={len(outages)}")
    except ConnectionError:
        raise  # Re-raise injected errors
    except Exception as e:
        error_count += 1
        log.error(f"Error calculating indices #{calculation_count}: {e}\n{traceback.format_exc()}")

def kafka_consumer_loop():
    """Background thread: consume outage events from Kafka."""
    time.sleep(30)  # Wait for Kafka
    try:
        consumer = KafkaConsumer(
            'outage.events',
            bootstrap_servers=KAFKA_BROKER,
            group_id='reliability-service',
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        log.info("Kafka consumer connected for outage.events")
        for message in consumer:
            try:
                event = message.value
                recent_events.append(event)
                if len(recent_events) > 200:
                    recent_events.pop(0)

                # Persist outage record
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO outages.outage_records (id, equipment_type, equipment_id, location, latitude, longitude,
                        start_time, end_time, status, cause, customers_affected, priority, crew_assigned, estimated_restoration)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status, end_time = EXCLUDED.end_time
                """, (
                    event.get('id'), event.get('equipmentType'), event.get('equipmentId'),
                    event.get('location'), event.get('latitude'), event.get('longitude'),
                    event.get('startTime'), event.get('endTime'), event.get('status'),
                    event.get('cause'), event.get('affectedCustomers'), event.get('priority'),
                    event.get('crewAssigned'), event.get('estimatedRestoration')
                ))
                conn.commit()
                cur.close()
                conn.close()

                # Recalculate
                calculate_indices()
                log.info(f"Processed outage event: {event.get('id')} status={event.get('status')}")
            except Exception as e:
                log.error(f"Error processing Kafka message: {e}")
    except Exception as e:
        log.warning(f"Kafka consumer not available, running in standalone mode: {e}")

def periodic_calculation():
    """Background thread: recalculate indices every 60 seconds."""
    time.sleep(20)
    while True:
        try:
            calculate_indices()
        except Exception as e:
            log.error(f"Periodic calculation failed: {e}")
        time.sleep(60)

# Start background threads
threading.Thread(target=kafka_consumer_loop, daemon=True).start()
threading.Thread(target=periodic_calculation, daemon=True).start()

# ============================================================
# API Endpoints
# ============================================================

@app.route('/api/reliability/calculate', methods=['POST'])
def trigger_calculate():
    """HTTP-triggered calculation cycle (for Dynatrace end-to-end tracing)."""
    log.info(f'POST /api/reliability/calculate - triggering calculation cycle #{calculation_count + 1}')

    # ~6% chance: simulate division by zero in CAIDI calculation
    if random.random() < 0.06:
        log.error("Division by zero in CAIDI calculation: total_customer_interruptions=0 "
                  "but total_customer_minutes > 0. Data inconsistency detected.")
        return jsonify({
            'error': 'CAIDI calculation error - division by zero',
            'type': 'ArithmeticError',
            'calculation': calculation_count + 1
        }), 500

    try:
        calculate_indices()
    except ConnectionError as e:
        return jsonify({'error': str(e), 'type': 'ConnectionError'}), 503
    except Exception as e:
        return jsonify({'error': str(e), 'type': 'CalculationError'}), 500

    return jsonify({
        'status': 'Calculation cycle complete',
        **current_indices
    })

@app.route('/api/reliability/indices', methods=['GET'])
def get_indices():
    log.info('GET /api/reliability/indices')
    return jsonify(current_indices)

@app.route('/api/reliability/history', methods=['GET'])
def get_history():
    days = int(request.args.get('days', 30))
    days = min(days, 90)

    # ~4% chance: simulate query timeout on large history
    if random.random() < 0.04:
        log.error(f"Query timeout fetching reliability history - "
                  f"statement canceled due to timeout after 5000ms. days={days}")
        return jsonify({'error': 'Query timeout on reliability history'}), 504

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT date::text, saidi, saifi, caidi, maifi, total_interruptions, total_customer_minutes
            FROM reliability.indices_daily
            ORDER BY date DESC LIMIT %s
        """, (days,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # Convert Decimal to float
        for row in rows:
            for k, v in row.items():
                if hasattr(v, 'is_finite'):
                    row[k] = float(v)
        log.info(f'GET /api/reliability/history days={days} count={len(rows)}')
        return jsonify(rows)
    except Exception as e:
        log.error(f'Error fetching history: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/reliability/trends', methods=['GET'])
def get_trends():
    """Monthly aggregated trends."""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT to_char(date, 'YYYY-MM') as month,
                   ROUND(AVG(saidi)::numeric, 4) as avg_saidi,
                   ROUND(AVG(saifi)::numeric, 4) as avg_saifi,
                   ROUND(AVG(caidi)::numeric, 4) as avg_caidi,
                   SUM(total_interruptions) as total_outages,
                   COUNT(*) as days_in_period
            FROM reliability.indices_daily
            GROUP BY to_char(date, 'YYYY-MM')
            ORDER BY month DESC LIMIT 12
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            for k, v in row.items():
                if hasattr(v, 'is_finite'):
                    row[k] = float(v)
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reliability/events', methods=['GET'])
def get_events():
    limit = min(int(request.args.get('limit', 50)), 200)
    return jsonify(recent_events[-limit:])

@app.route('/api/reliability/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'Healthy',
        'service': 'ReliabilityService',
        'lastCalculation': current_indices.get('last_calculated')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
