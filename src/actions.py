# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm actions."""

import logging
from typing import Iterator

import ops

from state import State

logger = logging.getLogger(__name__)

EMAIL_LIST_MAX = 50
EMAIL_LIST_SEPARATOR = ","


class Observer(ops.Object):
    """Indico charm actions observer."""

    def __init__(self, charm: ops.CharmBase, state: State):
        """Initialize the observer and register actions handlers.

        Args:
            charm: The parent charm to attach the observer to.
            state: The Indico charm state.
        """
        super().__init__(charm, "actions-observer")
        self.charm = charm
        self.state = state

        charm.framework.observe(charm.on.add_admin_action, self._add_admin_action)
        charm.framework.observe(charm.on.anonymize_user_action, self._anonymize_user_action)

    def _add_admin_action(self, event: ops.ActionEvent) -> None:
        """Add a new user to Indico.

        Args:
            event: Event triggered by the add_admin action
        """
        container = self.charm.unit.get_container("indico")
        indico_env_config = self._get_indico_env_config_str(container)

        cmd = [
            "/usr/local/bin/indico",
            "autocreate",
            "admin",
            event.params["email"],
            event.params["password"],
        ]

        if container.can_connect():
            process = container.exec(
                cmd,
                user="indico",
                working_dir="/srv/indico",
                environment=indico_env_config,
            )
            try:
                output = process.wait_output()
                event.set_results({"user": f"{event.params['email']}", "output": output})
            except ops.pebble.ExecError as ex:
                logger.exception("Action add-admin failed: %s", ex.stdout)

                event.fail(
                    # Parameter validation errors are printed to stdout
                    f"Failed to create admin {event.params['email']}: {ex.stdout!r}"
                )

    def _execute_anonymize_cmd(self, event: ops.ActionEvent) -> Iterator[str]:
        """Execute anonymize command for each email.

        Args:
            event (ActionEvent): Event triggered by the anonymize-user action

        Yields:
            Iterator[str]: Output of each command execution
        """
        container = self.charm.unit.get_container("indico")
        indico_env_config = self._get_indico_env_config_str(container)
        for email in event.params["email"].split(EMAIL_LIST_SEPARATOR):
            cmd = [
                "/usr/local/bin/indico",
                "anonymize",
                "user",
                email,
            ]

            if not container.can_connect():
                logger.error(
                    "Action anonymize-user failed: cannot connect to the Indico workload container"
                )
                self.unit.status = ops.WaitingStatus(
                    "Waiting to be able to connect to workload container"
                )
                return

            process = container.exec(
                cmd,
                user="indico",
                working_dir="/srv/indico",
                environment=indico_env_config,
            )
            try:
                out = process.wait_output()
                yield out[0].replace("\n", "")
            except ops.pebble.ExecError as ex:
                logger.exception("Action anonymize-user failed: %s", ex.stdout)
                fail_msg = f"Failed to anonymize user {event.params['email']}: {ex.stdout!r}"
                event.fail("Failed to anonymize one or more users, please verify the results.")
                yield fail_msg

    def _anonymize_user_action(self, event: ops.ActionEvent) -> None:
        """Anonymize user in Indico.

        If find an error, the action will fail. All the results will be set until the error
        has happened.

        Args:
            event: Event triggered by the anonymize-user action
        """
        if len(event.params["email"].split(EMAIL_LIST_SEPARATOR)) > EMAIL_LIST_MAX:
            max_reached_msg = (
                "Failed to anonymize user: "
                f"List of more than {EMAIL_LIST_MAX} emails are not allowed"
            )
            logger.error("Action anonymize-user failed: %s", max_reached_msg)
            event.fail(max_reached_msg)
            return
        output_list = list(self._execute_anonymize_cmd(event))
        event.set_results(
            {
                "user": f"{event.params['email']}",
                "output": EMAIL_LIST_SEPARATOR.join(output_list),
            }
        )
