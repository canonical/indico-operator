# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.s3_integrator.name
}

output "provides" {
  value = {
    s3_credentials = "s3-credentials"
  }
}

output "endpoints" {
  value = {
    s3_credentials = "s3-credentials"
  }
}
