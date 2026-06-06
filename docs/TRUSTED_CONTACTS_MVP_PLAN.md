# Trusted Contacts MVP — Plan

## Goal

Allow logged-in DavidAI users to add, edit, delete, list, and set a primary trusted contact.

**Status:** Implemented (MVP complete).

## Database model

`TrustedContact` (`trusted_contacts` table):

| Field | Type |
|-------|------|
| id | Integer PK |
| user_id | FK → users.id |
| full_name | String(255), required |
| phone_number | String(32), optional |
| email | String(255), optional |
| relationship | String(64), optional |
| is_primary | Boolean |
| created_at | DateTime |
| updated_at | DateTime |

Migration: `003_trusted_contacts`

## Routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/contacts` | List contacts + add form |
| POST | `/contacts/add` | Create contact |
| POST | `/contacts/edit/<id>` | Update contact |
| POST | `/contacts/delete/<id>` | Delete contact |
| POST | `/contacts/set-primary/<id>` | Set primary contact |

## Security

- Flask-Login required on all routes
- Contacts scoped to `current_user.id`
- Cross-user access returns "Contact not found"

## Validation

- `full_name` required
- At least `phone_number` or `email` required
- Email format validated
- Only one `is_primary=True` per user

## Future

- SOS button integration
- GPS location in alerts
- Twilio SMS notifications
- Email alerts via SendGrid or similar
