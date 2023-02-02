# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm unit tests."""

# pylint:disable=protected-access

import typing
from unittest.mock import DEFAULT, MagicMock, patch

from ops.charm import ActionEvent
from ops.model import Container
from ops.pebble import ExecError

from tests.unit._patched_charm import IndicoOperatorCharm
from tests.unit.test_base import TestBase


class TestActions(TestBase):
    """Indico charm unit tests."""

    @patch.object(Container, "exec")
    def test_refresh_external_resources_when_customization_and_plugins_set(self, mock_exec):
        """
        arrange: charm created and relations established
        act: configure the external resources and trigger the refresh action
        assert: the customization sources are pulled and the plugins upgraded
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))

        self.harness.disable_hooks()
        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.is_ready(
            [
                "nginx-prometheus-exporter",
                "indico",
                "indico-celery",
                "indico-nginx",
            ]
        )
        self.harness.update_config(
            {
                "customization_sources_url": "https://example.com/custom",
                "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
            }
        )

        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)
        charm._refresh_external_resources(MagicMock())

        mock_exec.assert_any_call(
            ["git", "pull"],
            working_dir="/srv/indico/custom",
            user="indico",
            environment={},
        )
        mock_exec.assert_any_call(
            ["pip", "install", "--upgrade", "git+https://example.git/#subdirectory=themes_cern"],
            environment={},
        )

    @patch.object(Container, "exec")
    def test_add_admin(self, mock_exec):
        """
        arrange: an email and a password
        act: when the _on_add_admin_action method is executed
        assert: the indico command to add the user is executed with the appropriate parameters.
        """

        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))

        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.is_ready(
            [
                "celery-prometheus-exporter",
                "statsd-prometheus-exporter",
                "nginx-prometheus-exporter",
                "indico",
                "indico-celery",
                "indico-nginx",
            ]
        )
        self.harness.disable_hooks()

        container = self.harness.model.unit.get_container("indico")

        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)

        email = "sample@email.com"
        password = "somepassword"  # nosec
        event = MagicMock(spec=ActionEvent)
        event.params = {
            "email": email,
            "password": password,
        }

        def event_store_failure(arg):
            event.fail_message = arg

        event.fail = event_store_failure

        indico_env_config = charm._get_indico_env_config_str(container)
        expected_cmd = [
            "/srv/indico/.local/bin/indico",
            "autocreate",
            "admin",
            email,
            password,
        ]

        charm._add_admin_action(event)

        mock_exec.assert_any_call(
            expected_cmd,
            user="indico",
            working_dir="/srv/indico",
            environment=indico_env_config,
        )

    @patch.object(Container, "exec")
    def test_add_admin_fail(self, mock_exec):
        """
        arrange: an email and a password
        act: when the _on_add_admin_action method is executed
        assert: the indico command to add the user is executed with the appropriate parameters.
        """

        mock_wo = MagicMock(
            return_value=("", None),
        )

        stdout_mock = "CRASH"

        # I'm disabling unused-argument here because some could be passed to the mock
        def mock_wo_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
            if isinstance(mock_wo.cmd, list) and "autocreate" in mock_wo.cmd:
                raise ExecError(command=mock_wo.cmd, exit_code=42, stdout=stdout_mock, stderr="")
            return DEFAULT

        mock_wo.side_effect = mock_wo_side_effect

        # I'm disabling unused-argument here because some could be passed to the mock
        def mock_exec_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
            mock_wo.cmd = args[0]
            return DEFAULT

        mock_exec.side_effect = mock_exec_side_effect
        mock_exec.return_value = MagicMock(
            wait_output=mock_wo,
        )

        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.is_ready(
            [
                "celery-prometheus-exporter",
                "statsd-prometheus-exporter",
                "nginx-prometheus-exporter",
                "indico",
                "indico-celery",
                "indico-nginx",
            ]
        )
        self.harness.disable_hooks()

        container = self.harness.model.unit.get_container("indico")

        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)

        email = "sample@email.com"
        password = "somepassword"  # nosec
        event = MagicMock(spec=ActionEvent)
        event.params = {
            "email": email,
            "password": password,
        }

        def event_store_failure(arg):
            event.fail_message = arg

        event.fail = event_store_failure

        indico_env_config = charm._get_indico_env_config_str(container)
        expected_cmd = [
            "/srv/indico/.local/bin/indico",
            "autocreate",
            "admin",
            email,
            password,
        ]

        charm._add_admin_action(event)
        assert event.fail_message == f"Failed to create admin {email}: '{stdout_mock}'"

        mock_exec.assert_any_call(
            expected_cmd,
            user="indico",
            working_dir="/srv/indico",
            environment=indico_env_config,
        )
