"""Trusted contacts routes — user-scoped CRUD."""

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.contacts_service import (
    add_contact,
    delete_contact,
    get_user_contact,
    list_user_contacts,
    set_primary_contact,
    update_contact,
    validate_contact_payload,
)


def register_contacts_routes(app: Flask) -> None:
    @app.route("/contacts")
    @login_required
    def contacts():
        user_contacts = list_user_contacts(current_user.id)
        return render_template(
            "contacts.html",
            page="contacts",
            contacts=user_contacts,
        )

    @app.route("/contacts/add", methods=["POST"])
    @login_required
    def contacts_add():
        ok, error, payload = validate_contact_payload(
            request.form.get("full_name"),
            request.form.get("phone_number"),
            request.form.get("email"),
            request.form.get("relationship"),
        )
        if not ok:
            flash(error, "error")
            return redirect(url_for("contacts"))

        set_primary = request.form.get("is_primary") == "on"
        add_contact(current_user.id, payload, set_primary=set_primary)
        flash("Trusted contact added.", "success")
        return redirect(url_for("contacts"))

    @app.route("/contacts/edit/<int:contact_id>", methods=["POST"])
    @login_required
    def contacts_edit(contact_id: int):
        contact = get_user_contact(current_user.id, contact_id)
        if contact is None:
            flash("Contact not found.", "error")
            return redirect(url_for("contacts"))

        ok, error, payload = validate_contact_payload(
            request.form.get("full_name"),
            request.form.get("phone_number"),
            request.form.get("email"),
            request.form.get("relationship"),
        )
        if not ok:
            flash(error, "error")
            return redirect(url_for("contacts"))

        update_contact(contact, payload)
        flash("Contact updated.", "success")
        return redirect(url_for("contacts"))

    @app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
    @login_required
    def contacts_delete(contact_id: int):
        contact = get_user_contact(current_user.id, contact_id)
        if contact is None:
            flash("Contact not found.", "error")
            return redirect(url_for("contacts"))

        delete_contact(contact)
        flash("Contact deleted.", "success")
        return redirect(url_for("contacts"))

    @app.route("/contacts/set-primary/<int:contact_id>", methods=["POST"])
    @login_required
    def contacts_set_primary(contact_id: int):
        contact = set_primary_contact(current_user.id, contact_id)
        if contact is None:
            flash("Contact not found.", "error")
            return redirect(url_for("contacts"))

        flash(f"{contact.full_name} is now your primary contact.", "success")
        return redirect(url_for("contacts"))
