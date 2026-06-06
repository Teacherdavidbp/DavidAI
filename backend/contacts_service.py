"""Trusted contacts business logic and validation."""

from __future__ import annotations

import re
from datetime import datetime

from backend.extensions import db
from database.models import TrustedContact

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_text(value: str | None, *, max_len: int) -> str:
    return (value or "").strip()[:max_len]


def _clean_email(value: str | None) -> str:
    return _clean_text(value, max_len=255).lower()


def _clean_phone(value: str | None) -> str:
    return _clean_text(value, max_len=32)


def validate_contact_payload(
    full_name: str | None,
    phone_number: str | None,
    email: str | None,
    relationship: str | None,
) -> tuple[bool, str, dict]:
    name = _clean_text(full_name, max_len=255)
    phone = _clean_phone(phone_number)
    mail = _clean_email(email)
    rel = _clean_text(relationship, max_len=64) or None

    if not name:
        return False, "Full name is required.", {}

    if not phone and not mail:
        return False, "Provide at least a phone number or email address.", {}

    if mail and not EMAIL_RE.match(mail):
        return False, "Enter a valid email address.", {}

    return True, "", {
        "full_name": name,
        "phone_number": phone or None,
        "email": mail or None,
        "relationship": rel,
    }


def list_user_contacts(user_id: int) -> list[TrustedContact]:
    return list(
        db.session.scalars(
            db.select(TrustedContact)
            .filter_by(user_id=user_id)
            .order_by(TrustedContact.is_primary.desc(), TrustedContact.full_name.asc())
        ).all()
    )


def get_user_contact(user_id: int, contact_id: int) -> TrustedContact | None:
    return db.session.scalar(
        db.select(TrustedContact).filter_by(id=contact_id, user_id=user_id)
    )


def add_contact(user_id: int, payload: dict, *, set_primary: bool = False) -> TrustedContact:
    contact = TrustedContact(user_id=user_id, **payload)
    db.session.add(contact)
    db.session.flush()

    if set_primary or not _user_has_primary(user_id):
        _set_primary_for_user(user_id, contact.id)

    db.session.commit()
    db.session.refresh(contact)
    return contact


def update_contact(contact: TrustedContact, payload: dict) -> TrustedContact:
    contact.full_name = payload["full_name"]
    contact.phone_number = payload["phone_number"]
    contact.email = payload["email"]
    contact.relationship = payload["relationship"]
    contact.updated_at = datetime.utcnow()
    db.session.commit()
    db.session.refresh(contact)
    return contact


def delete_contact(contact: TrustedContact) -> None:
    was_primary = contact.is_primary
    user_id = contact.user_id
    db.session.delete(contact)
    db.session.commit()

    if was_primary:
        next_contact = db.session.scalar(
            db.select(TrustedContact)
            .filter_by(user_id=user_id)
            .order_by(TrustedContact.created_at.asc())
            .limit(1)
        )
        if next_contact:
            _set_primary_for_user(user_id, next_contact.id)
            db.session.commit()


def set_primary_contact(user_id: int, contact_id: int) -> TrustedContact | None:
    contact = get_user_contact(user_id, contact_id)
    if contact is None:
        return None
    _set_primary_for_user(user_id, contact.id)
    db.session.commit()
    db.session.refresh(contact)
    return contact


def _user_has_primary(user_id: int) -> bool:
    return (
        db.session.scalar(
            db.select(db.func.count())
            .select_from(TrustedContact)
            .filter_by(user_id=user_id, is_primary=True)
        )
        or 0
    ) > 0


def _set_primary_for_user(user_id: int, contact_id: int) -> None:
    for contact in db.session.scalars(
        db.select(TrustedContact).filter_by(user_id=user_id)
    ).all():
        contact.is_primary = contact.id == contact_id
        if contact.id == contact_id:
            contact.updated_at = datetime.utcnow()
