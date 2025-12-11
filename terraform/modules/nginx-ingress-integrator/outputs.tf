# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.nginx_ingress_integrator.name
}

output "requires" {
  value = {
    certificates = "certificates"
  }
}

output "provides" {
  value = {
    ingress     = "ingress"
    nginx_route = "nginx-route"
  }
}

output "endpoints" {
  value = {
    certificates = "certificates"
    ingress      = "ingress"
    nginx_route  = "nginx-route"
  }
}
