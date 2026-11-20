#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.flask
from paas_charm.charm_state import CharmState

logger = logging.getLogger(__name__)

EMAIL_LIST_SEPARATOR = ","
EMAIL_LIST_MAX = 50
INDICO_WRAPPER = "/srv/indico/start-indico.sh"


class IndicoCharm(paas_charm.flask.Charm):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on["add-admin"].action, self._add_admin_action)
        self.framework.observe(self.on["anonymize-user"].action, self._anonymize_user_action)
        self.framework.observe(
            self.on["refresh-external-resources"].action,
            self._refresh_external_resources_action,
        )

    def _missing_required_integrations(self, charm_state: CharmState) -> typing.Generator:
        """Get the missing required integrations, including the cache backend.

        paas-charm does not enforce the `valkey` integration, and `redis` is optional
        only to allow in-place refreshes, so one of them must be required here.

        Args:
            charm_state: the charm state.

        Yields:
            Names of the missing required integrations.
        """
        yield from super()._missing_required_integrations(charm_state)
        if not charm_state.integrations.valkey and not charm_state.integrations.redis:
            yield "valkey or redis"

    def is_ready(self) -> bool:
        """Check if the charm is ready to start the workload application.

        Returns:
            True if the charm is ready to start the workload application.
        """
        if not super().is_ready():
            return False
        integrations = self._create_charm_state().integrations
        if integrations.valkey and integrations.redis:
            # indico.conf prefers VALKEY_DB_* over REDIS_DB_*, so keep the workload
            # running on Valkey instead of stopping it. This lets operators add
            # valkey and then remove redis without downtime.
            logger.warning(
                "Both valkey and redis are integrated, using valkey; remove the redis integration"
            )
        return True

    def _add_admin_action(self, event: ops.ActionEvent) -> None:
        """Add a new admin user to Indico.

        Args:
            event: Event triggered by the add-admin action.
        """
        container = self._container
        if not container.can_connect():
            event.fail("Cannot connect to the Indico workload container")
            return
        email = event.params["email"]
        cmd = [INDICO_WRAPPER, "indico", "autocreate", "admin", email, event.params["password"]]
        process = container.exec(
            cmd,
            user="_daemon_",
            working_dir="/flask/app",
            environment=self._gen_environment(),
        )
        try:
            output = process.wait_output()
            event.set_results({"user": email, "output": output[0]})
        except ops.pebble.ExecError as ex:
            logger.exception("Action add-admin failed: %s", ex.stdout)
            event.fail(f"Failed to create admin {email}: {ex.stdout!r}")

    def _execute_anonymize_cmd(self, event: ops.ActionEvent) -> typing.Iterator[str]:
        """Execute the anonymize command for each email.

        Args:
            event: Event triggered by the anonymize-user action.

        Yields:
            Output of each command execution.
        """
        container = self._container
        for email in event.params["email"].split(EMAIL_LIST_SEPARATOR):
            cmd = [INDICO_WRAPPER, "indico", "anonymize", "user", email]
            process = container.exec(
                cmd,
                user="_daemon_",
                working_dir="/flask/app",
                environment=self._gen_environment(),
            )
            try:
                out = process.wait_output()
                yield out[0].replace("\n", "")
            except ops.pebble.ExecError as ex:
                logger.exception("Action anonymize-user failed: %s", ex.stdout)
                event.fail("Failed to anonymize one or more users, please verify the results.")
                yield f"Failed to anonymize user {email}: {ex.stdout!r}"

    def _anonymize_user_action(self, event: ops.ActionEvent) -> None:
        """Anonymize one or more Indico users.

        Args:
            event: Event triggered by the anonymize-user action.
        """
        container = self._container
        if not container.can_connect():
            event.fail("Cannot connect to the Indico workload container")
            return
        emails = event.params["email"].split(EMAIL_LIST_SEPARATOR)
        if len(emails) > EMAIL_LIST_MAX:
            event.fail(f"Failed to anonymize user: more than {EMAIL_LIST_MAX} emails not allowed")
            return
        output_list = list(self._execute_anonymize_cmd(event))
        event.set_results(
            {
                "user": event.params["email"],
                "output": EMAIL_LIST_SEPARATOR.join(output_list),
            }
        )

    def _refresh_external_resources_action(self, event: ops.ActionEvent) -> None:
        """Reinstall/upgrade the external plugins by restarting the workload.

        Clears the plugin install marker so `start-indico.sh` reinstalls
        `external_plugins` on the next service start, then restarts services.

        Args:
            event: Event triggered by the refresh-external-resources action.
        """
        container = self._container
        if not container.can_connect():
            event.fail("Cannot connect to the Indico workload container")
            return
        container.exec(["rm", "-f", "/srv/indico/plugins/.installed"]).wait()
        self.restart()
        event.set_results({"result": "external plugins refresh triggered"})


if __name__ == "__main__":
    ops.main(IndicoCharm)
