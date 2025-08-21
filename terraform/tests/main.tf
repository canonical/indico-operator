# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "channel" {
  description = "The channel to use when deploying a charm."
  type        = string
  default     = "latest/edge"
}

variable "revision" {
  description = "Revision number of the charm."
  type        = number
  default     = null
}

terraform {
  required_providers {
    juju = {
      version = "~> 0.21.1"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

module "indico" {
  source      = "./.."
  app_name    = "indico"
  channel     = var.channel
  model       = "prod-events-example"
  revision    = var.revision
  constraints = "arch=amd64"
}
