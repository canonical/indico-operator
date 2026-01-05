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
      version = ">= 1.1.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

data "juju_model" "example" {
  name  = "prod-events-example"
  owner = "admin"
}

module "indico" {
  source      = "./.."
  app_name    = "indico"
  channel     = var.channel
  model_uuid  = data.juju_model.example.uuid
  revision    = var.revision
  constraints = "arch=amd64"
}
