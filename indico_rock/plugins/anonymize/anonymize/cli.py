#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Create users non-interactively."""

import click
from hashlib import sha512
from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.modules.users.util import search_users
from indico.util.date_time import now_utc


@cli_group(name="anonymize")
def cli():
    """Anonymize users non-interactively."""

# Extracted from:
# https://github.com/bpedersen2/indico-cron-advanced-cleaner/
def anonymize_deleted_user(user):
    """Anonymize user by erasing specific attributes."""

    _anon_attrs = ['first_name', 'last_name', 'phone', 'address',]
    _clear_attrs_str = ['affiliation', 'email', 'secondary_emails', ]
    _clear_attrs_set = ['favorite_users', 'favorite_categories', 'identities']
    _clear_attrs_list = ['old_api_keys',]


    for attr in _clear_attrs_str:
        setattr(user, attr, '')

    for attr in _clear_attrs_set:
        setattr(user, attr, set())

    for attr in _clear_attrs_list:
        setattr(user, attr, list())

    for attr in _anon_attrs:
        val = getattr(user, attr)
        new_hash = sha512(val.encode('utf-8')+now_utc().isoformat().encode('utf-8')).hexdigest()[:12]
        setattr(user, attr, new_hash)

@cli.command("user")
@click.argument("email", type=str)
@click.pass_context
def anonymize_user(ctx, email):
    """Anonymize user non-interactively."""

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

    if not user.is_deleted:
        click.secho("User was not anonymized", fg="red")
        ctx.exit(1)

    click.secho(f'User with email "{email}" correctly anonymized', fg="green")
