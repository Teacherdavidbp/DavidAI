# SOS Notifications MVP — Plan

## Purpose

When a user triggers an SOS alert, DavidAI records who **would** be notified via their primary trusted contact. Phase 2 stores a simulated SMS notification — **no real SMS, email, or push is sent**.

## Database model

`SOSNotification` (`sos_notifications`):

| Field | Description |
|-------|-------------|
| id | Primary key |
| user_id | Alert owner |
| sos_alert_id | Linked SOS alert |
| contact_id | Primary trusted contact |
| channel | `sms`, `email`, or `push` |
| status | `pending`, `simulated`, `sent`, `failed` |
| message | Full alert text with map link |
| created_at | Record created |
| updated_at | Last update |

**MVP values:** `channel=sms`, `status=simulated`

Migration: `005_sos_notifications`

## Notification flow

```
User presses SOS
    → Browser geolocation
    → POST /sos/trigger
    → SOSAlert created (active)
    → get_primary_contact_for_user()
         ├─ Found → SOSNotification (simulated SMS)
         └─ Missing → warning returned, no notification
    → UI shows contact name, channel, status, message preview
```

## Simulated SMS mode

Message format:

```
DavidAI SOS Alert: {user_email} triggered an SOS alert at {timestamp}. Location: https://maps.google.com/?q={lat},{lng}
```

The message is stored in PostgreSQL only. No external API calls.

## Future Twilio integration

- Read `TWILIO_*` from `.env` (never commit)
- On SOS trigger, send real SMS to primary contact `phone_number`
- Update status: `pending` → `sent` or `failed`
- Retry and delivery logging

## Future email integration

- Channel `email` to contact `email` address
- Provider: SendGrid / SMTP via env vars
- HTML template with map link

## Future push notifications

- Channel `push` for mobile app (Phase 6)
- FCM / APNs integration

## Related

- `docs/SOS_ALERT_MVP_PLAN.md` — Phase 1 GPS capture
- `docs/TRUSTED_CONTACTS_MVP_PLAN.md` — Primary contact selection
