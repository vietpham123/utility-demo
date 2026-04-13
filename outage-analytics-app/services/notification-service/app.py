import os, json, time, logging, threading, random, traceback
from datetime import datetime, timezone
from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras
from celery import Celery

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
log = logging.getLogger('notification-service')

# ============================================================
# Configuration
# ============================================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'timescaledb'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'dbname': os.getenv('DB_NAME', 'utilitydb'),
    'user': os.getenv('DB_USER', 'utilityuser'),
    'password': os.getenv('DB_PASSWORD', os.getenv('DB_PASSWORD'))
}
RABBITMQ_URL = os.getenv('RABBITMQ_URL', os.getenv('RABBITMQ_URL'))

# Celery configuration
celery_app = Celery('notifications', broker=RABBITMQ_URL, backend='rpc://')
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='notifications',
    task_routes={
        'send_sms': {'queue': 'notifications.sms'},
        'send_email': {'queue': 'notifications.email'},
        'send_push': {'queue': 'notifications.push'},
        'send_ivr': {'queue': 'notifications.ivr'}
    }
)

# ============================================================
# In-memory state
# ============================================================
notification_log = []
notification_counter = 0
error_count = 0
delivery_stats = {
    'sms': {'sent': 0, 'delivered': 0, 'failed': 0},
    'email': {'sent': 0, 'delivered': 0, 'failed': 0},
    'push': {'sent': 0, 'delivered': 0, 'failed': 0},
    'ivr': {'sent': 0, 'delivered': 0, 'failed': 0}
}

# Simulated customer contact preferences
customer_contacts = {}
for i in range(1, 31):
    cid = f'CUST-{str(i).zfill(3)}'
    prefs = random.sample(['sms', 'email', 'push'], k=random.randint(1, 3))
    customer_contacts[cid] = {
        'customerId': cid,
        'name': f'Customer {i}',
        'phone': f'+1-555-{str(random.randint(1000, 9999))}',
        'email': f'customer{i}@genericutility.com',
        'preferences': prefs,
        'optedIn': True
    }

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# ============================================================
# Celery Tasks (simulated delivery)
# ============================================================
@celery_app.task(name='send_sms', bind=True, max_retries=3)
def send_sms(self, notification):
    """Simulate SMS delivery via carrier gateway."""
    log.debug(f"Celery task send_sms: {notification.get('notificationId')} to {notification.get('phone')}")

    # ~6% chance: SMS gateway timeout
    if random.random() < 0.06:
        delivery_stats['sms']['failed'] += 1
        log.error(f"SMS gateway timeout: Twilio API returned 504 for {notification.get('phone')}. "
                  f"Notification {notification.get('notificationId')}")
        raise self.retry(countdown=10)

    time.sleep(random.uniform(0.1, 0.5))  # Simulate API call
    delivery_stats['sms']['sent'] += 1
    delivery_stats['sms']['delivered'] += 1
    log.info(f"SMS delivered: {notification.get('notificationId')} to {notification.get('phone')}")
    return {'status': 'delivered', 'channel': 'sms', 'notificationId': notification.get('notificationId')}


@celery_app.task(name='send_email', bind=True, max_retries=3)
def send_email(self, notification):
    """Simulate email delivery via SMTP relay."""
    log.debug(f"Celery task send_email: {notification.get('notificationId')} to {notification.get('email')}")

    # ~4% chance: SMTP relay failure
    if random.random() < 0.04:
        delivery_stats['email']['failed'] += 1
        log.error(f"SMTP relay error: Connection refused to smtp.genericutility.com:587. "
                  f"Notification {notification.get('notificationId')}")
        raise self.retry(countdown=15)

    time.sleep(random.uniform(0.2, 0.8))  # Simulate SMTP send
    delivery_stats['email']['sent'] += 1
    delivery_stats['email']['delivered'] += 1
    log.info(f"Email delivered: {notification.get('notificationId')} to {notification.get('email')}")
    return {'status': 'delivered', 'channel': 'email', 'notificationId': notification.get('notificationId')}


@celery_app.task(name='send_push', bind=True, max_retries=2)
def send_push(self, notification):
    """Simulate push notification via Firebase/APNS."""
    log.debug(f"Celery task send_push: {notification.get('notificationId')} to {notification.get('customerId')}")

    # ~8% chance: Push token expired
    if random.random() < 0.08:
        delivery_stats['push']['failed'] += 1
        log.warning(f"Push notification failed: Device token expired for {notification.get('customerId')}. "
                    f"FCM returned NotRegistered. Notification {notification.get('notificationId')}")
        return {'status': 'failed', 'channel': 'push', 'reason': 'token_expired'}

    time.sleep(random.uniform(0.05, 0.3))
    delivery_stats['push']['sent'] += 1
    delivery_stats['push']['delivered'] += 1
    log.info(f"Push delivered: {notification.get('notificationId')} to {notification.get('customerId')}")
    return {'status': 'delivered', 'channel': 'push', 'notificationId': notification.get('notificationId')}


@celery_app.task(name='send_ivr', bind=True, max_retries=2)
def send_ivr(self, notification):
    """Simulate IVR outbound call for critical outages."""
    log.debug(f"Celery task send_ivr: {notification.get('notificationId')} to {notification.get('phone')}")

    # ~10% chance: Call failed (no answer, busy)
    if random.random() < 0.10:
        delivery_stats['ivr']['failed'] += 1
        reason = random.choice(['no_answer', 'busy', 'voicemail_full'])
        log.warning(f"IVR call failed: {reason} for {notification.get('phone')}. "
                    f"Notification {notification.get('notificationId')}")
        return {'status': 'failed', 'channel': 'ivr', 'reason': reason}

    time.sleep(random.uniform(0.5, 2.0))  # Simulate call setup
    delivery_stats['ivr']['sent'] += 1
    delivery_stats['ivr']['delivered'] += 1
    log.info(f"IVR call completed: {notification.get('notificationId')} to {notification.get('phone')}")
    return {'status': 'delivered', 'channel': 'ivr', 'notificationId': notification.get('notificationId')}


# ============================================================
# Notification Logic
# ============================================================
def create_notification(event_type, outage_data, extra=None):
    """Create and queue notifications for affected customers."""
    global notification_counter, error_count

    notification_counter += 1
    log.debug(f"Creating notifications #{notification_counter} for event: {event_type}, outage: {outage_data.get('outageId')}")

    # ~5% chance: customer lookup failure
    if random.random() < 0.05:
        error_count += 1
        log.error(f"Customer lookup service timeout: Failed to resolve affected customers for outage "
                  f"{outage_data.get('outageId')}. PostgreSQL query exceeded 5000ms timeout. "
                  f"Error count: {error_count}")
        return []

    # Determine affected customers (simulate lookup based on affected count)
    affected_count = outage_data.get('affectedCustomers', 10)
    num_customers = min(affected_count, 30)  # Cap at our 30 simulated customers
    affected_customer_ids = [f'CUST-{str(i).zfill(3)}' for i in random.sample(range(1, 31), min(num_customers, 30))]

    notifications = []
    templates = {
        'outage_detected': {
            'subject': 'Power Outage Alert',
            'sms': 'GenericUtility Alert: Power outage detected in {location}. Estimated restoration: {etr}. Track: gu.co/outage/{outageId}',
            'email_body': 'We are aware of a power outage affecting your area ({location}). Our crew ({crewName}) has been dispatched. Estimated restoration time: {etr}.',
            'push_title': 'Power Outage in Your Area',
            'push_body': 'Outage detected in {location}. ETR: {etr}'
        },
        'crew_dispatched': {
            'subject': 'Crew Dispatched to Your Area',
            'sms': 'GenericUtility: Crew {crewName} dispatched to {location}. ETR: {etr}. Updates: gu.co/outage/{outageId}',
            'email_body': 'A repair crew ({crewName}) has been dispatched to address the outage in {location}. Estimated restoration: {etr}.',
            'push_title': 'Repair Crew Dispatched',
            'push_body': '{crewName} dispatched. ETR: {etr}'
        },
        'crew_arrived': {
            'subject': 'Repair Crew On-Site',
            'sms': 'GenericUtility: Crew {crewName} is now on-site at {location}. Working to restore power. ETR: {etr}',
            'email_body': 'Our repair crew ({crewName}) has arrived at the outage location in {location} and is working to restore power.',
            'push_title': 'Crew Arrived On-Site',
            'push_body': '{crewName} on-site in {location}'
        },
        'etr_update': {
            'subject': 'Updated Restoration Estimate',
            'sms': 'GenericUtility: Updated ETR for outage in {location}: {etr}. Track: gu.co/outage/{outageId}',
            'email_body': 'The estimated restoration time for the outage in {location} has been updated to {etr}.',
            'push_title': 'ETR Updated',
            'push_body': 'New ETR for {location}: {etr}'
        },
        'power_restored': {
            'subject': 'Power Restored',
            'sms': 'GenericUtility: Power has been restored in {location}. Thank you for your patience.',
            'email_body': 'We are pleased to inform you that power has been restored in {location}. If you are still experiencing issues, please contact us at 1-800-GENERIC.',
            'push_title': 'Power Restored!',
            'push_body': 'Power restored in {location}'
        }
    }

    template = templates.get(event_type, templates['outage_detected'])
    merge_data = {**outage_data, **(extra or {})}

    for cid in affected_customer_ids:
        contact = customer_contacts.get(cid)
        if not contact or not contact.get('optedIn'):
            continue

        for channel in contact['preferences']:
            notification_counter += 1
            notif = {
                'notificationId': f'NOTIF-{str(notification_counter).zfill(6)}',
                'customerId': cid,
                'outageId': outage_data.get('outageId'),
                'eventType': event_type,
                'channel': channel,
                'status': 'queued',
                'createdAt': datetime.now(timezone.utc).isoformat(),
                'phone': contact.get('phone'),
                'email': contact.get('email')
            }

            # Format message
            try:
                if channel == 'sms':
                    notif['message'] = template['sms'].format(**merge_data)
                elif channel == 'email':
                    notif['subject'] = template['subject'].format(**merge_data)
                    notif['message'] = template['email_body'].format(**merge_data)
                elif channel == 'push':
                    notif['title'] = template['push_title'].format(**merge_data)
                    notif['message'] = template['push_body'].format(**merge_data)
            except KeyError as e:
                notif['message'] = f'Outage update for {outage_data.get("location", "your area")}'
                log.debug(f"Template merge missing key {e}, using fallback message")

            # Queue via Celery (or simulate if Celery not connected)
            try:
                if channel == 'sms':
                    send_sms.delay(notif)
                elif channel == 'email':
                    send_email.delay(notif)
                elif channel == 'push':
                    send_push.delay(notif)
                notif['status'] = 'sent'
                delivery_stats[channel]['sent'] += 1
                delivery_stats[channel]['delivered'] += 1
            except Exception as e:
                # Celery not available — simulate inline
                notif['status'] = 'sent'
                delivery_stats[channel]['sent'] += 1
                delivery_stats[channel]['delivered'] += 1
                log.debug(f"Celery unavailable, simulated {channel} delivery for {notif['notificationId']}")

            notifications.append(notif)
            notification_log.append(notif)

    # Trim log
    if len(notification_log) > 2000:
        del notification_log[:len(notification_log) - 2000]

    log.info(f"Created {len(notifications)} notifications for {event_type}", extra={
        'outageId': outage_data.get('outageId'),
        'affectedCustomers': len(affected_customer_ids),
        'channels': {ch: len([n for n in notifications if n['channel'] == ch]) for ch in ['sms', 'email', 'push']}
    })

    return notifications


# ============================================================
# DB Setup
# ============================================================
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS outages.customer_notifications (
                notification_id VARCHAR(20) PRIMARY KEY,
                customer_id VARCHAR(20),
                outage_id VARCHAR(20),
                event_type VARCHAR(50),
                channel VARCHAR(20),
                status VARCHAR(20) DEFAULT 'queued',
                message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                delivered_at TIMESTAMPTZ
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        log.info('Database table customer_notifications ready')
    except Exception as e:
        log.warn(f'Database table creation failed: {e}')


# ============================================================
# API Endpoints
# ============================================================

@app.route('/api/notifications/simulate', methods=['POST'])
def simulate_notifications():
    """HTTP-triggered notification cycle (for gateway orchestration)."""
    log.info('POST /api/notifications/simulate - triggering notification cycle')

    # ~7% chance: RabbitMQ broker unreachable
    if random.random() < 0.07:
        error_count_local = error_count + 1
        log.error(f"RabbitMQ broker unreachable during notification cycle: "
                  f"[Errno 111] Connection refused to rabbitmq:5672. Error #{error_count_local}")

    # ~3% chance: template rendering engine failure
    if random.random() < 0.03:
        log.error("Notification template rendering engine error: "
                  "Jinja2 UndefinedError: 'etr' is undefined in template 'outage_detected.html'")
        return jsonify({'error': 'Template rendering failure', 'type': 'RenderError'}), 500

    results = {'created': 0, 'channels': {'sms': 0, 'email': 0, 'push': 0}}

    # Create some sample notifications based on recent activity
    sample_outage = {
        'outageId': f'OUT-{str(random.randint(1, 200)).zfill(3)}',
        'location': random.choice(['Chicago, IL', 'Baltimore, MD', 'Philadelphia, PA', 'Washington, DC', 'New York, NY', 'Boston, MA', 'Atlanta, GA', 'Miami, FL', 'Dallas, TX', 'Houston, TX', 'Nashville, TN', 'Charlotte, NC', 'Orlando, FL', 'Detroit, MI', 'Cleveland, OH', 'Pittsburgh, PA', 'St. Louis, MO', 'Minneapolis, MN']),
        'etr': datetime.now(timezone.utc).isoformat(),
        'crewName': random.choice(['Alpha Team', 'Beta Team', 'Delta Team', 'Gamma Team']),
        'affectedCustomers': random.randint(50, 2000)
    }
    event_type = random.choice(['outage_detected', 'crew_dispatched', 'etr_update', 'power_restored'])
    notifs = create_notification(event_type, sample_outage)
    results['created'] = len(notifs)
    for n in notifs:
        if n['channel'] in results['channels']:
            results['channels'][n['channel']] += 1

    results['totalNotifications'] = len(notification_log)
    results['deliveryStats'] = delivery_stats

    log.info('Notification cycle complete', extra={'results': results})
    res = jsonify({'status': 'Notification cycle complete', **results})
    return res


@app.route('/api/notifications/dispatch', methods=['POST'])
def handle_dispatch():
    """Called by crew-dispatch-service when a crew is dispatched."""
    data = request.get_json() or {}
    log.info(f"Dispatch notification received: {data.get('dispatchId')} for outage {data.get('outageId')}")

    # ~4% chance: database write failure during notification persistence
    if random.random() < 0.04:
        log.error(f"Failed to persist notification to database: "
                  f"psycopg2.errors.SerializationFailure: could not serialize access. "
                  f"Dispatch {data.get('dispatchId')}")

    notifs = create_notification('crew_dispatched', {
        'outageId': data.get('outageId', ''),
        'location': data.get('location', ''),
        'etr': data.get('etr', ''),
        'crewName': data.get('crewName', ''),
        'affectedCustomers': data.get('affectedCustomers', 0)
    })
    return jsonify({'status': 'Dispatch notifications sent', 'count': len(notifs)})


@app.route('/api/notifications/crew-arrived', methods=['POST'])
def handle_crew_arrived():
    """Called when crew arrives on-site."""
    data = request.get_json() or {}
    log.info(f"Crew arrived notification: {data.get('dispatchId')}")
    notifs = create_notification('crew_arrived', {
        'outageId': data.get('outageId', ''),
        'location': data.get('location', ''),
        'etr': data.get('etr', ''),
        'crewName': data.get('crewName', ''),
        'affectedCustomers': data.get('affectedCustomers', 10)
    })
    return jsonify({'status': 'Arrival notifications sent', 'count': len(notifs)})


@app.route('/api/notifications/restored', methods=['POST'])
def handle_restored():
    """Called when power is restored."""
    data = request.get_json() or {}
    log.info(f"Power restored notification: outage {data.get('outageId')}")
    notifs = create_notification('power_restored', {
        'outageId': data.get('outageId', ''),
        'location': data.get('location', ''),
        'crewName': data.get('crewName', ''),
        'etr': data.get('restoredAt', ''),
        'affectedCustomers': data.get('affectedCustomers', 10)
    })
    return jsonify({'status': 'Restoration notifications sent', 'count': len(notifs)})


@app.route('/api/notifications/log', methods=['GET'])
def get_notification_log():
    limit = min(int(request.args.get('limit', 50)), 200)

    # ~3% chance: slow log query
    if random.random() < 0.03:
        delay = 2 + random.random() * 3
        log.warning(f"Slow notification log query: sequential scan on customer_notifications, delay={delay:.1f}s")
        time.sleep(delay)

    log.info(f'GET /api/notifications/log limit={limit}')
    return jsonify(notification_log[-limit:])


@app.route('/api/notifications/stats', methods=['GET'])
def get_notification_stats():
    by_type = {}
    by_channel = {}
    for n in notification_log:
        et = n.get('eventType', 'unknown')
        ch = n.get('channel', 'unknown')
        by_type[et] = by_type.get(et, 0) + 1
        by_channel[ch] = by_channel.get(ch, 0) + 1

    return jsonify({
        'totalNotifications': len(notification_log),
        'deliveryStats': delivery_stats,
        'byEventType': by_type,
        'byChannel': by_channel,
        'customersReachable': len([c for c in customer_contacts.values() if c['optedIn']]),
        'avgChannelsPerCustomer': round(sum(len(c['preferences']) for c in customer_contacts.values()) / max(len(customer_contacts), 1), 1)
    })


@app.route('/api/notifications/customers', methods=['GET'])
def get_customers():
    """List customer notification preferences."""
    return jsonify(list(customer_contacts.values()))


@app.route('/api/notifications/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'Healthy',
        'service': 'NotificationService',
        'totalNotifications': len(notification_log),
        'deliveryStats': delivery_stats,
        'celeryBroker': RABBITMQ_URL.split('@')[1] if '@' in RABBITMQ_URL else 'unknown'
    })


# ============================================================
# Startup
# ============================================================
init_db()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port)
