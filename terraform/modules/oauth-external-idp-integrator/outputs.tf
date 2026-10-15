# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.oauth_integrator.name
}

output "provides" {
  value = {
    oauth = "oauth"
  }
}

output "endpoints" {
  value = {
    oauth = "oauth"
  }
}
