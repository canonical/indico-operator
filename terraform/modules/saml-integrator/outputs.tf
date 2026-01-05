# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.saml_integrator.name
}

output "provides" {
  value = {
    saml = "saml"
  }
}
