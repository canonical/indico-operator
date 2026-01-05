# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.indico.name
}

output "endpoints" {
  value = {
    grafana_dashboard = "grafana-dashboard"
    metrics_endpoint  = "metrics-endpoint"
    database          = "database"
    nginx_route       = "nginx-route"
    redis_broker      = "redis-broker"
    redis_cache       = "redis-cache"
    s3                = "s3"
    saml              = "saml"
    smtp_legacy       = "smtp-legacy"
    logging           = "logging"
  }
}
