# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "s3_integrator" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "s3-integrator"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config = var.config
  units  = var.units
  provisioner "local-exec" {
    # There's currently no way to wait for the charm to be idle, hence the sleep
    command = "sleep 60; juju run ${self.name}/leader sync-s3-credentials access-key=${var.s3_access_key} secret-key=${var.s3_secret_key}; "
  }
}
