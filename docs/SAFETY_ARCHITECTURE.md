# DavidAI Safety Architecture

Architecture for the DavidAI Safety MVP — GPS, SOS, trusted contacts, and subscription billing.

## Overview

```
User Device (DavidAI App)
    ├── GPS Module → location updates
    ├── SOS Button → Emergency Alert System
    ├── Trusted Contacts → notification targets
    ├── AI Chat → Ollama (local) / DeepSeek (future)
    └── Subscription → Stripe £3.99/month (future)
```

## GPS tracking workflow

1. User grants location permission on login.
2. App requests GPS coordinates via browser Geolocation API (web) or native SDK (mobile).
3. Backend stores last known location on `SOSAlert` or dedicated location table (future).
4. On SOS trigger, current lat/lng attached to alert payload.
5. Trusted contacts receive location link in SMS/email (Twilio — future).

```
[User] → [Get GPS] → [POST /api/sos] → [Store lat/lng] → [Notify contacts]
```

## SOS workflow

1. User presses **SOS** button in Safety Center.
2. Client captures GPS + optional message.
3. `POST /api/sos` creates `SOSAlert` record (status: `active`).
4. Emergency Alert System queues notifications to all trusted contacts.
5. User sees confirmation and alert ID.
6. Contacts acknowledge or alert auto-escalates (future).
7. User or admin resolves alert → status `resolved`.

## Trusted contact workflow

1. User adds contact: name, phone, email.
2. Stored in `trusted_contacts` table linked to `users`.
3. User sets SMS/email notification preferences per contact.
4. On SOS, all contacts with `notify_sms` / `notify_email` enabled are targeted.
5. Twilio sends SMS with location and message (Phase 2).

## Subscription — £3.99/month

| Item | Detail |
|------|--------|
| Plan | `safety_monthly` |
| Price | £3.99 GBP / month |
| Features | SOS, GPS sharing, trusted contacts, AI chat |
| Payment | Stripe Checkout (future) |
| DB table | `subscriptions` |

Workflow (future):

1. User selects Safety plan on Profile page.
2. Redirect to Stripe Checkout session.
3. Webhook confirms payment → `subscriptions.status = active`.
4. SOS features unlocked.

## Future Twilio integration

- **Purpose:** SMS alerts to trusted contacts on SOS.
- **Env vars:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- **Endpoint:** `POST /api/notifications/sms`
- **Template:** "DavidAI SOS from {user}: {message}. Location: {maps_link}"

## Future Stripe integration

- **Purpose:** £3.99/month subscription billing.
- **Env vars:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`
- **Endpoints:**
  - `POST /api/billing/checkout` — create session
  - `POST /api/billing/webhook` — handle events
- **Webhook events:** `checkout.session.completed`, `customer.subscription.deleted`

## Database

- Primary DB: `davidai_dev`
- Models: `database/models.py` (User, TrustedContact, SOSAlert, Subscription)
- Config: `database/config.py`

## AI integration

| Phase | Engine | Use |
|-------|--------|-----|
| Now | Ollama `qwen2.5:7b` | Local chat testing via AI Lab Dashboard |
| Later | DeepSeek API | Cloud reasoning for safety advice |

System prompt includes real UK date/time from AI Lab `/api/time`.

## Related files

- `03_PROJECTS/DavidAI/backend/app.py` — Flask scaffold
- `05_DATABASES/Schemas/create_databases.sql`
- `database/models.py`
