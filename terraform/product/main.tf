# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Juju model

resource "juju_model" "indico" {
  name = local.model.name

  cloud {
    name   = local.model.cloud_name
    region = local.model.cloud_region
  }

  config      = local.config_model
  constraints = local.model.constraints

  lifecycle {
    prevent_destroy = true
  }
}

# Modules

module "indico" {
  source      = "./.."
  app_name    = local.app_names.indico
  channel     = local.channels.indico
  config      = local.config_indico
  constraints = var.constraints.indico
  model_uuid  = juju_model.indico.uuid
  revision    = local.revisions.indico
  units       = local.units.indico
}

module "lego" {
  count      = local.enable.nginx_ingress_integrator && local.enable.lego ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/lego"
  channel    = local.channels.lego
  revision   = local.revisions.lego
  config     = local.config_lego
}

resource "juju_secret" "lego_credentials" {
  count      = local.enable.nginx_ingress_integrator && local.enable.lego ? 1 : 0
  model_uuid = juju_model.indico.uuid
  name       = local.lego_secret.name
  value      = local.lego_secret.value
}

resource "juju_access_secret" "lego_credentials_access" {
  count      = local.enable.nginx_ingress_integrator && local.enable.lego ? 1 : 0
  model_uuid = juju_model.indico.uuid
  applications = [
    module.lego[0].app_name
  ]
  secret_id = juju_secret.lego_credentials[0].secret_id
}

module "nginx_ingress_integrator" {
  count      = local.enable.nginx_ingress_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/nginx-ingress-integrator"
  app_name   = local.app_names.nginx_ingress_integrator
  channel    = local.channels.nginx_ingress_integrator
  revision   = local.revisions.nginx_ingress_integrator
  config     = local.config_nginx_ingress_integrator
}

module "redis_cache" {
  count      = local.enable.redis_cache ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/redis-k8s"
  app_name   = local.app_names.redis_cache
  channel    = local.channels.redis_cache
  revision   = local.revisions.redis_cache
}

module "redis_broker" {
  count      = local.enable.redis_broker ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/redis-k8s"
  app_name   = local.app_names.redis_broker
  channel    = local.channels.redis_broker
  revision   = local.revisions.redis_broker
}


module "s3_integrator_media" {
  count         = local.enable.s3_integrator_media ? 1 : 0
  model_uuid    = juju_model.indico.uuid
  source        = "../modules/s3-integrator"
  app_name      = local.app_names.s3_integrator_media
  channel       = local.channels.s3_integrator_media
  revision      = local.revisions.s3_integrator_media
  config        = local.config_s3_integrator_media
  s3_access_key = local.credentials.s3_access_key
  s3_secret_key = local.credentials.s3_secret_key
}

module "smtp_integrator" {
  count      = local.enable.smtp_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/smtp-integrator"
  channel    = local.channels.smtp_integrator
  revision   = local.revisions.smtp_integrator
  config     = local.config_smtp_integrator
}

module "local_saml_integrator" {
  count      = local.enable.local_saml_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid
  source     = "../modules/saml-integrator"
  channel    = local.channels.local_saml_integrator
  revision   = local.revisions.local_saml_integrator
  config     = local.config_local_saml_integrator
}

module "local_postgresql" {
  count        = local.enable.local_postgresql ? 1 : 0
  model_uuid   = juju_model.indico.uuid
  source       = "../modules/postgresql-k8s"
  base         = "ubuntu@22.04"
  app_name     = local.app_names.local_postgresql
  channel      = local.channels.local_postgresql
  revision     = local.revisions.local_postgresql
  config       = local.config_local_postgresql
  storage_size = "1G"
}

# Integrations with offers

resource "juju_integration" "indico_postgresql" {
  count      = local.integrate_offers.postgresql ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.database
  }

  application {
    offer_url = local.offer_urls.postgresql
  }
}

resource "juju_integration" "indico_prometheus" {
  count      = local.integrate_offers.prometheus ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.metrics_endpoint
  }

  application {
    offer_url = local.offer_urls.prometheus
  }
}

resource "juju_integration" "indico_grafana" {
  count      = local.integrate_offers.grafana ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.grafana_dashboard
  }

  application {
    offer_url = local.offer_urls.grafana
  }
}

resource "juju_integration" "indico_saml" {
  count      = local.integrate_offers.saml_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.saml
  }

  application {
    offer_url = local.offer_urls.saml_integrator
  }
}


# Integrations between modules

resource "juju_integration" "indico_nginx_ingress_integrator" {
  count      = local.enable.nginx_ingress_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.nginx_route
  }

  application {
    name     = module.nginx_ingress_integrator[0].app_name
    endpoint = module.nginx_ingress_integrator[0].endpoints.nginx_route
  }
}

resource "juju_integration" "indico_s3_integrator_media" {
  count      = local.enable.s3_integrator_media ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.s3
  }

  application {
    name     = module.s3_integrator_media[0].app_name
    endpoint = module.s3_integrator_media[0].endpoints.s3_credentials
  }
}

resource "juju_integration" "indico_smtp_integrator" {
  count      = local.enable.smtp_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.smtp_legacy
  }

  application {
    name     = module.smtp_integrator[0].app_name
    endpoint = module.smtp_integrator[0].endpoints.smtp
  }
}

resource "juju_integration" "indico_local_saml_integrator" {
  count      = local.enable.local_saml_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.saml
  }

  application {
    name     = module.local_saml_integrator[0].app_name
    endpoint = module.local_saml_integrator[0].provides.saml
  }
}

resource "juju_integration" "indico_redis_cache" {
  count      = local.enable.redis_cache ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.redis_cache
  }

  application {
    name     = module.redis_cache[0].app_name
    endpoint = module.redis_cache[0].endpoints.redis
  }
}

resource "juju_integration" "indico_redis_broker" {
  count      = local.enable.redis_broker ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.redis_broker
  }

  application {
    name     = module.redis_broker[0].app_name
    endpoint = module.redis_broker[0].endpoints.redis
  }
}

resource "juju_integration" "nginx_lego" {
  count      = local.enable.lego && local.enable.nginx_ingress_integrator ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.nginx_ingress_integrator[0].app_name
    endpoint = module.nginx_ingress_integrator[0].endpoints.certificates
  }

  application {
    name     = module.lego[0].app_name
    endpoint = module.lego[0].endpoints.certificates
  }
}

resource "juju_integration" "indico_local_postgresql" {
  count      = local.enable.local_postgresql ? 1 : 0
  model_uuid = juju_model.indico.uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.database
  }

  application {
    name     = module.local_postgresql[0].application_name
    endpoint = module.local_postgresql[0].provides.database
  }
}
