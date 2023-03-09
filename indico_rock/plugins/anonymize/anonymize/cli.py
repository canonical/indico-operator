#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Anonymize users non-interactively."""

import click
from hashlib import sha512
from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.users import User
from indico.modules.users.util import search_users
from indico.util.date_time import now_utc
from indico.modules.users import User
import re

CLEAN_ATTRS_STR = ['affiliation', 'email', 'secondary_emails', ]
CLEAN_ATTRS_SET= ['favorite_users', 'favorite_categories', 'identities']
CLEAN_ATTRS_LIST = ['old_api_keys',]
CLEAN_ATTRS_ANON = ['first_name', 'last_name', 'phone', 'address',]

@cli_group(name="anonymize")
def cli():
    """Anonymize users non-interactively."""

# Extracted from:
# https://github.com/bpedersen2/indico-cron-advanced-cleaner/
def anonymize_deleted_user(user: User):
    """Anonymize user by erasing specific attributes.

    Args:
        user: Indico user
    """

    for attr in CLEAN_ATTRS_STR:
        setattr(user, attr, '')

    for attr in CLEAN_ATTRS_SET:
        setattr(user, attr, set())

    for attr in CLEAN_ATTRS_LIST:
        setattr(user, attr, list())

    for attr in CLEAN_ATTRS_ANON:
        val = getattr(user, attr)
        new_hash = sha512(val.encode('utf-8')+now_utc().isoformat().encode('utf-8')).hexdigest()[:12]
        getattr(user, attr, new_hash)

def is_anonymized(user: User) -> bool:
    """Check if user is anonymized.

    Args:
        user: Indico user
    Returns:
        If user is anonymized
    """

    for attr in CLEAN_ATTRS_STR:
        if getattr(user, attr, '') != '':
            return False

    for attr in CLEAN_ATTRS_SET:
        if getattr(user, attr, set()):
            return False

    for attr in CLEAN_ATTRS_LIST:
        if getattr(user, attr, list()):
            return False

    for attr in CLEAN_ATTRS_ANON:
        hash_regex = re.compile('^[a-fA-F0-9]{12}$')
        if not hash_regex.match(getattr(user, attr)):
            return False

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
        click.secho("User not found", fg="red")
        ctx.exit(1)
    user = user.first()
    # First we mark as deleted so won't appear in any form
    user.is_deleted = True
    anonymize_deleted_user(user)
    db.session.commit()  # pylint: disable=no-member

    # Validate the changes
    res = search_users(
        exact=True,
        include_deleted=True,
        include_pending=False,
        include_blocked=False,
        external=False,
        allow_system_user=False,
        email=email,
    )

    user = res.pop()

    if not user.is_deleted or not is_anonymized(user):
        click.secho("User was not anonymized", fg="red")
        ctx.exit(1)

    click.secho(f'User with email "{email}" correctly anonymized', fg="green")
