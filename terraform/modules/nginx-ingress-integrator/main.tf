# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "nginx_ingress_integrator" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "nginx-ingress-integrator"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config = var.config
  units  = var.units
  trust  = true
}
