# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.indico.name
}

output "endpoints" {
  # Relation endpoint names as declared by the 12-factor (flask-framework)
  # indico charm (see the charm's metadata.yaml). Kept in sync with the built
  # charm: postgresql/redis/s3/smtp/saml/oauth/ingress + observability.
  value = {
    grafana_dashboard = "grafana-dashboard"
    metrics_endpoint  = "metrics-endpoint"
    logging           = "logging"
    postgresql        = "postgresql"
    redis             = "redis"
    s3                = "s3"
    smtp              = "smtp"
    saml              = "saml"
    oauth             = "oauth"
    ingress           = "ingress"
  }
}
