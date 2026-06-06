"""DavidAI SQLAlchemy models — Safety MVP."""

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship
from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trusted_contacts: Mapped[list["TrustedContact"]] = orm_relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = orm_relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sos_alerts: Mapped[list["SOSAlert"]] = orm_relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sos_notifications: Mapped[list["SOSNotification"]] = orm_relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = orm_relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self) -> str:
        return self.full_name or self.email.split("@")[0]


class TrustedContact(db.Model):
    __tablename__ = "trusted_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    relationship: Mapped[str | None] = mapped_column(String(64))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = orm_relationship(back_populates="trusted_contacts")
    sos_notifications: Mapped[list["SOSNotification"]] = orm_relationship(
        back_populates="contact"
    )


class SOSAlert(db.Model):
    __tablename__ = "sos_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = orm_relationship(back_populates="sos_alerts")
    notifications: Mapped[list["SOSNotification"]] = orm_relationship(
        back_populates="sos_alert", cascade="all, delete-orphan"
    )


class SOSNotification(db.Model):
    __tablename__ = "sos_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    sos_alert_id: Mapped[int] = mapped_column(ForeignKey("sos_alerts.id"), nullable=False, index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("trusted_contacts.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    provider_sid: Mapped[str | None] = mapped_column(String(64))
    provider_detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = orm_relationship(back_populates="sos_notifications")
    sos_alert: Mapped["SOSAlert"] = orm_relationship(back_populates="notifications")
    contact: Mapped["TrustedContact"] = orm_relationship(back_populates="sos_notifications")


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(64), default="safety_monthly", nullable=False)
    price_gbp: Mapped[float] = mapped_column(Float, default=3.99, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="inactive", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = orm_relationship(back_populates="subscriptions")


class Conversation(db.Model):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="DavidAI Chat", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = orm_relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = orm_relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(64))
    search_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    conversation: Mapped["Conversation"] = orm_relationship(back_populates="messages")
