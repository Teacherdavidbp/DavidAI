# Safety Center Architecture

## Purpose

The Safety Center (`/safety-center`) is the central hub for reviewing and managing all safety-related activity in DavidAI. It aggregates trusted contacts, SOS alerts, SMS notifications, and location history into a single dashboard without replacing existing dedicated pages (`/contacts`, `/sos`, `/safety`).

## Data Flow

```
User (Flask-Login session)
        │
        ▼
GET /safety-center  (safety_center_routes.py)
        │
        ▼
safety_center_service.py
        │
        ├── get_safety_summary(user_id)
        ├── get_recent_contacts(user_id)
        ├── get_recent_sos_alerts(user_id)
        ├── get_recent_notifications(user_id)
        └── get_location_history(user_id)
        │
        ▼
PostgreSQL (scoped by user_id)
  • trusted_contacts
  • sos_alerts
  • sos_notifications
        │
        ▼
safety_center.html + safety_center.css + safety_center.js
```

### Widgets

| Widget | Data source | Limit |
|--------|-------------|-------|
| Safety Overview | Aggregated counts | — |
| Trusted Contacts | `trusted_contacts` | All contacts |
| SOS History | `sos_alerts` | Latest 10 |
| SMS History | `sos_notifications` | Latest 20 |
| Notification Status | `sos_notifications` | Latest 10 |
| Location History | `sos_alerts` (lat/lng) | Latest 20 |

Google Maps links use `https://maps.google.com/?q={lat},{lng}`. Location history is **read-only** — no live tracking in this MVP.

## Security

- **Authentication:** Flask-Login `@login_required` on `/safety-center`
- **Authorization:** Every query filters by `current_user.id` — users only see their own contacts, alerts, notifications, and locations
- **Secrets:** Twilio credentials are never loaded into templates; only `twilio_mode` label (live / simulated / misconfigured) is shown
- **Provider details:** SMS provider metadata from notifications is not surfaced on the Safety Center dashboard (available on `/sos` only)

## Related Pages (unchanged)

| Route | Purpose |
|-------|---------|
| `/contacts` | Full CRUD for trusted contacts |
| `/sos` | Trigger SOS, resolve alerts, notification detail |
| `/safety` | Legacy safety overview placeholder |

## Future Roadmap

1. **Safety Check-In MVP** — scheduled check-ins with escalation to trusted contacts
2. **Live location sharing** — optional real-time GPS stream during active SOS
3. **Email / push channels** — extend notification widgets beyond SMS
4. **Export** — CSV/PDF export of safety history
5. **Family dashboard** — delegated view for trusted contacts (with consent)
6. **Subscription gating** — tie advanced safety features to £3.99/month plan
