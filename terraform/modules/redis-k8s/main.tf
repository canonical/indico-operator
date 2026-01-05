# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "redis_k8s" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "redis-k8s"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }

  config             = var.config
  units              = var.units
  storage_directives = var.storage
}
