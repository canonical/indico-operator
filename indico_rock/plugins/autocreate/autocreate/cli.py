#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Create users non-interactively."""

import click
from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.modules.users.util import search_users


@cli_group(name="autocreate")
def cli():
    """Create users non-interactively."""


@cli.command("admin")
@click.argument("email", type=str)
@click.argument("password", type=str)
@click.pass_context
def create_admin(ctx, email, password) -> None:
    """Create a new admin user non-interactively.

    Args:
        ctx: Click's CLI context passed as a parameter.
        email: Indico user's email.
        password: Indico user's password
    """
    email = email.lower()
    username = email
    first_name = "unknown"
    last_name = "unknown"
    affiliation = "unknown"

    if User.query.filter(User.all_emails == email, ~User.is_deleted, ~User.is_pending).has_rows():
        click.secho("This user already exists", fg="red")
        ctx.exit(1)

    if password == "":
        click.secho("Password should not be empty", fg="red")
        ctx.exit(1)

    if Identity.query.filter_by(provider="indico", identifier=username).has_rows():
        click.secho("Username already exists", fg="red")
        ctx.exit(1)

    identity = Identity(provider="indico", identifier=username, password=password)
    user = create_user(
        email,
        {"first_name": first_name, "last_name": last_name, "affiliation": affiliation},
        identity,
    )
    user.is_admin = True

    # db.session has add()
    db.session.add(user)  # pylint: disable=no-member
    # db.session has commit()
    db.session.commit()  # pylint: disable=no-member

    # search the created user
    res = search_users(
        exact=True,
        include_deleted=False,
        include_pending=False,
        include_blocked=False,
        external=False,
        allow_system_user=False,
        email=email,
    )

    if not res:
        click.secho("Admin was not correctly created", fg="red")
        ctx.exit(1)

    user = res.pop()

    if not user.is_admin:
        click.secho("Created user is not admin", fg="red")
        ctx.exit(1)

    click.secho(f'Admin with email "{user.email}" correctly created', fg="green")
