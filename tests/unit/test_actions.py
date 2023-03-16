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
            "/usr/local/bin/indico",
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
            "/usr/local/bin/indico",
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

    @patch.object(Container, "exec")
    def test_anonymize_user(self, mock_exec):
        """
        arrange: an email
        act: when the _on_anonymize_user_action method is executed
        assert: the indico command to anonymize the user is executed with the appropriate
            parameters and the event results is set as expected
        """
        # Set Indico
        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)
        charm._get_installed_plugins = MagicMock(return_value="")
        charm._get_indico_secret_key_from_relation = MagicMock(return_value="")
        self.harness.container_pebble_ready("indico")

        # Set Mock
        email = "sample@email.com"
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=(f"{email}", None)))

        # Set and trigger the event
        mock_event = MagicMock(spec=ActionEvent)
        mock_event.params = {
            "email": email,
        }
        charm._anonymize_user_action(mock_event)

        # Check if command was called
        expected_cmd = [
            "/usr/local/bin/indico",
            "anonymize",
            "user",
            email,
        ]
        container = self.harness.model.unit.get_container("indico")
        indico_env_config = charm._get_indico_env_config_str(container)
        mock_exec.assert_any_call(
            expected_cmd,
            user="indico",
            working_dir="/srv/indico",
            environment=indico_env_config,
        )

        # Check if event results was properly set
        mock_event.set_results.assert_called_with(
            {"user": f"{email}", "output": (f"{email}", None)}
        )

    @patch.object(Container, "exec")
    def test_anonymize_user_list(self, mock_exec):
        """
        arrange: an list of emails
        act: when the _on_anonymize_user_action method is executed
        assert: the indico command to anonymize the user is executed with the appropriate
            parameters and the event results is set as expected
        """
        # Set Indico
        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)
        charm._get_installed_plugins = MagicMock(return_value="")
        charm._get_indico_secret_key_from_relation = MagicMock(return_value="")
        self.harness.container_pebble_ready("indico")

        # Set Mock
        emails = "sample@email.com,sample1@email.com"

        # Set and trigger the event
        mock_event = MagicMock(spec=ActionEvent)
        mock_event.params = {
            "email": emails,
        }
        first_email = MagicMock(wait_output=MagicMock(return_value=("sample@email.com", None)))
        second_email = MagicMock(wait_output=MagicMock(return_value=("sample1@email.com", None)))
        mock_exec.side_effect = [first_email, second_email]
        charm._anonymize_user_action(mock_event)

        def validate_command(email: str):
            # Check if command was called
            expected_cmd = [
                "/usr/local/bin/indico",
                "anonymize",
                "user",
                email,
            ]
            container = self.harness.model.unit.get_container("indico")
            indico_env_config = charm._get_indico_env_config_str(container)
            mock_exec.assert_any_call(
                expected_cmd,
                user="indico",
                working_dir="/srv/indico",
                environment=indico_env_config,
            )

        for email in emails.split(","):
            validate_command(email)

        # Check if event results was properly set
        mock_event.set_results.assert_called_with(
            {"user": f"{emails}", "output": (f"{emails}", None)}
        )

    @patch.object(Container, "exec")
    def test_anonymize_user_fail(self, mock_exec):
        """
        arrange: an email
        act: when the _on_anonymize_user_action method is executed
        assert: the indico command to anonymize the user is executed with the appropriate
            parameters and the event results is set as expected
        """
        # Set Indico
        charm: IndicoOperatorCharm = typing.cast(IndicoOperatorCharm, self.harness.charm)
        charm._get_installed_plugins = MagicMock(return_value="")
        charm._get_indico_secret_key_from_relation = MagicMock(return_value="")
        self.harness.container_pebble_ready("indico")

        # Set Mock
        email = "sample@email.com"
        error_msg = "Execution error"
        expected_cmd = [
            "/usr/local/bin/indico",
            "anonymize",
            "user",
            email,
        ]
        expected_exception = ExecError(
            command=" ".join(expected_cmd), exit_code=42, stdout=f"{error_msg}", stderr=""
        )
        wait_output = MagicMock(side_effect=expected_exception)
        mock_exec.return_value = MagicMock(wait_output=wait_output)
        # Set and trigger the event
        mock_event = MagicMock(spec=ActionEvent)
        mock_event.params = {
            "email": email,
        }
        charm._anonymize_user_action(mock_event)

        # Check if command was called
        container = self.harness.model.unit.get_container("indico")
        indico_env_config = charm._get_indico_env_config_str(container)
        mock_exec.assert_any_call(
            expected_cmd,
            user="indico",
            working_dir="/srv/indico",
            environment=indico_env_config,
        )

        # Check if event fail was properly set
        expected_argument = f"Failed to anonymize user {email}: '{error_msg}'"
        # Pylint does not understand that the mock supports this call
        mock_event.fail.assert_called_with(expected_argument)  # pylint: disable=no-member

        # Check if event results was properly set
        mock_event.set_results.assert_called_with(
            {
                "user": f"{email}",
                "output": (f"Failed to anonymize user {email}: '{error_msg}'", None),
            }
        )
