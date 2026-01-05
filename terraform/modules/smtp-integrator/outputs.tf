# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.smtp_integrator.name
}

output "provides" {
  value = {
    smtp        = "smtp"
    smtp_legacy = "smtp-legacy"
  }
}

output "endpoints" {
  value = {
    smtp        = "smtp"
    smtp_legacy = "smtp-legacy"
  }
}
