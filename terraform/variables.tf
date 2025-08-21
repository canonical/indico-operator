# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "app_name" {
  description = "Name of the application in the Juju model."
  type        = string
  default     = "synapse"
}

variable "base" {
  description = "The operating system on which to deploy"
  type        = string
  default     = "ubuntu@20.04"
}

variable "channel" {
  description = "The channel to use when deploying a charm."
  type        = string
  default     = "latest/stable"
}

variable "config" {
  description = "Application config."
  type        = map(string)
  default     = {}
}

variable "constraints" {
  description = "Juju constraints to apply for this application."
  type        = string
  default     = ""
}

variable "model" {
  description = "Reference to a `juju_model`."
  type        = string
  default     = ""
}

variable "revision" {
  description = "Revision number of the charm."
  type        = number
  default     = null
}

variable "storage" {
  description = "Map of storage used by the application."
  type        = map(string)
  default     = {}
}

variable "units" {
  description = "Number of units to deploy."
  type        = number
  default     = 1
}
