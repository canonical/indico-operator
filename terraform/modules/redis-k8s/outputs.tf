# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.redis_k8s.name
}

output "provides" {
  value = {
    redis = "redis"
  }
}

output "endpoints" {
  value = {
    redis = "redis"
  }
}
