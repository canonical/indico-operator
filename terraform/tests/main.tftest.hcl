# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variables {
  channel = "latest/edge"
  # renovate: depName="indico"
  revision = 263
}

run "basic_deploy" {
  assert {
    condition     = module.indico.app_name == "indico"
    error_message = "Indico app_name did not match expected"
  }
}
