# SOS Alert MVP — Plan

## Phase 1 (Implemented)

Allow logged-in users to trigger an SOS alert that captures:

- Timestamp (`created_at`)
- User ID (`user_id`)
- GPS coordinates (`latitude`, `longitude`)
- Alert status (`active` / `resolved`)

Stored in PostgreSQL `sos_alerts`. **No Twilio, email, or SMS.**

### Routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/sos` | SOS page with button, GPS status, alerts |
| POST | `/sos/trigger` | Create active alert (JSON coordinates) |
| POST | `/sos/resolve/<id>` | Mark alert resolved |

### Validation

- Flask-Login required
- User-scoped alerts only
- GPS coordinates required and range-checked
- Browser handles permission denied / unavailable / timeout

---

## Phase 2 — Trusted Contact notifications (Implemented)

- On SOS trigger, load user's primary trusted contact
- Create `SOSNotification` record (`channel=sms`, `status=simulated`)
- Store message with Google Maps link — **no real SMS sent**
- Warning if no primary contact configured

See `docs/SOS_NOTIFICATIONS_MVP_PLAN.md`

## Phase 3 — Email alerts

- Send email to trusted contacts via provider (SendGrid / SMTP env vars)
- Include map link from lat/lng

## Phase 4 — Twilio SMS

- SMS primary and secondary contacts on SOS
- `TWILIO_*` credentials in `.env` only

## Phase 5 — Real-time location tracking

- Periodic GPS updates while alert is active
- Location trail table or JSON history

## Phase 6 — Mobile app

- Native iOS/Android SOS with background location
- Push notifications to trusted contacts
