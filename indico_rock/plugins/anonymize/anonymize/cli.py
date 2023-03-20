#!/usr/bin/env python3 -W ignore::UserWarning
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Anonymize users non-interactively."""

from hashlib import sha512

import click
from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.users import User
from indico.util.date_time import now_utc

CLEAN_ATTRS = {
    "affiliation": str(),
    "email": str(),
    "secondary_emails": str(),
    "favorite_users": set(),
    "favorite_categories": set(),
    "identities": set(),
    "old_api_keys": [],
}
HASH_ATTRS = ["first_name", "last_name", "phone", "address"]


@cli_group(name="anonymize")
def cli():
    """Anonymize users non-interactively."""


# Extracted from:
# https://github.com/bpedersen2/indico-cron-advanced-cleaner/
def _hash(val: str) -> str:
    """Create hash of val.

    Args:
        val: The string from the hash should be created
    Returns:
        First 12 characters from encoded data in hexadecimal format
    """
    return sha512(val.encode("utf-8") + now_utc().isoformat().encode("utf-8")).hexdigest()[:12]


# Based on:
# https://github.com/bpedersen2/indico-cron-advanced-cleaner/
def anonymize_deleted_user(user: User):
    """Anonymize user by erasing specific attributes.

    Args:
        user: Indico user
    """
    for attr, anonymize_val in CLEAN_ATTRS.items():
        current_val = getattr(user, attr)
        setattr(user, attr, anonymize_val)
    for attr in HASH_ATTRS:
        current_val = getattr(user, attr)
        setattr(user, attr, _hash(current_val))


def anonymize_registration(registration: Registration):
    """Anonymize registration by changing specific attributes.

    Args:
        registration (Registration): User registration_
    """
    for fid, rdata in registration.data_by_field.items():
        fieldtype = RegistrationFormField.get(oid=fid).input_type
        if fieldtype in ("text", "textarea"):
            rdata.data = _hash(rdata.data)
        elif fieldtype == "email":
            rdata.data = f"{_hash(rdata.data)}@invalid.invalid"
        elif fieldtype == "phone":
            rdata.data = "(+00) 0000000"
        elif fieldtype == "date":
            # Keep dates for now
            pass
        elif fieldtype == "country":
            # Keep country for now
            pass
        # other field types are not touched (choice, multiple choice, radio)

    registration.first_name = _hash(registration.first_name)
    registration.last_name = _hash(registration.last_name)
    registration.email = _hash(registration.email)
    if registration.user:
        registration.user = None


# Based on:
# https://github.com/bpedersen2/indico-cron-advanced-cleaner/
def anonymize_registrations(user: User):
    """Anonymize user by erasing registrations attributes.

    Args:
        user: Indico user
    """
    registrations = Registration.query.filter(Registration.user_id == user.id)
    for registration in registrations:
        anonymize_registration(registration)
    # db.session has commit()
    db.session.commit()  # pylint: disable=no-member


@cli.command("user")
@click.argument("email", type=str)
@click.pass_context
def anonymize_user(ctx, email):
    """Anonymize user non-interactively.

    Args:
        ctx: context
        email: email of the user to be anonymized
    """

    email = email.lower()

    if email == "":
        click.secho("E-mail should not be empty", fg="red")
        ctx.exit(1)

    users = User.query.filter(User.all_emails == email)
    if not users.has_rows():
        click.secho("User not found", fg="yellow")
        ctx.exit(0)
    user = users.first()

    # We mark as deleted so won't appear in search users forms
    user.is_deleted = True
    anonymize_deleted_user(user)
    # Anonymize registrations
    anonymize_registrations(user)

    # Validate the changes
    users = User.query.filter(User.all_emails == email)
    if users.has_rows():
        click.secho("User was not anonymized", fg="red")
        ctx.exit(1)

    click.secho(f'User with email "{email}" correctly anonymized', fg="green")
