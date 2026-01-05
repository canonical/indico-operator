# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "lego" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "lego"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config = var.config
  units  = var.units
}
