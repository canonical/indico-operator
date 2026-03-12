# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    channel    = "latest/edge"
    # renovate: depName="indico"
    revision = 310
  }

  assert {
    condition     = output.app_name == "indico"
    error_message = "Indico app_name did not match expected"
  }
}
