# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "oauth_integrator" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "oauth-external-idp-integrator"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config = var.config
  units  = var.units
}
