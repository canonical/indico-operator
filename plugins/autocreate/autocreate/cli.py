import click
from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user


@cli_group(name="autocreate")
def cli():
    """Create users non-interactively."""


@cli.command("user")
@click.argument("email", type=str)
@click.argument("password", type=str)
@click.option("--first-name", help="First name of the user", type=str)
@click.option("--last-name", help="Last name of the user", type=str)
@click.option("--affiliation", help="Affiliation of the user", type=str)
@click.option("--admin/--no-admin", "grant_admin", is_flag=True, help="Grant admin rights")
def autocreate(email, password, first_name, last_name, affiliation, grant_admin):
    """Create a new user non-interactively."""

    user_type = "user" if not grant_admin else "admin"
    email = email.lower()
    username = email
    first_name = first_name or "unknown"
    last_name = last_name or "unknown"
    affiliation = affiliation or "unknown"

    if User.query.filter(User.all_emails == email, ~User.is_deleted, ~User.is_pending).has_rows():
        return

    if password == "":
        return

    if Identity.query.filter_by(provider="indico", identifier=username).has_rows():
        click.secho("Username already exists", fg="red")

    identity = Identity(provider="indico", identifier=username, password=password)
    user = create_user(
        email,
        {"first_name": first_name, "last_name": last_name, "affiliation": affiliation},
        identity,
    )
    user.is_admin = grant_admin

    db.session.add(user)
    db.session.commit()
