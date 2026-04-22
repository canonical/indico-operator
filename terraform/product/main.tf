# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Modules

module "indico" {
  source      = "./.."
  app_name    = local.app_names.indico
  channel     = local.channels.indico
  config      = local.config_indico
  constraints = var.constraints.indico
  model_uuid  = var.juju_model_uuid
  revision    = local.revisions.indico
  units       = local.units.indico
}

module "redis_cache" {
  model_uuid = var.juju_model_uuid
  source     = "../modules/redis-k8s"
  app_name   = local.app_names.redis_cache
  channel    = local.channels.redis_cache
  revision   = local.revisions.redis_cache
}

module "redis_broker" {
  model_uuid = var.juju_model_uuid
  source     = "../modules/redis-k8s"
  app_name   = local.app_names.redis_broker
  channel    = local.channels.redis_broker
  revision   = local.revisions.redis_broker
}


module "s3_integrator_media" {
  model_uuid    = var.juju_model_uuid
  source        = "../modules/s3-integrator"
  app_name      = local.app_names.s3_integrator_media
  channel       = local.channels.s3_integrator_media
  revision      = local.revisions.s3_integrator_media
  config        = local.config_s3_integrator_media
  s3_access_key = local.credentials.s3_access_key
  s3_secret_key = local.credentials.s3_secret_key
}

module "smtp_integrator" {
  model_uuid = var.juju_model_uuid
  source     = "../modules/smtp-integrator"
  channel    = local.channels.smtp_integrator
  revision   = local.revisions.smtp_integrator
  config     = local.config_smtp_integrator
}

module "local_saml_integrator" {
  model_uuid = var.juju_model_uuid
  source     = "../modules/saml-integrator"
  channel    = local.channels.local_saml_integrator
  revision   = local.revisions.local_saml_integrator
  config     = local.config_local_saml_integrator
}

resource "juju_integration" "indico_saml" {
  model_uuid = var.juju_model_uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.saml
  }

  application {
    name = module.local_saml_integrator.app_name
    endpoint = module.local_saml_integrator.endpoints.saml
  }
}

resource "juju_integration" "indico_s3_integrator_media" {
  model_uuid = var.juju_model_uuid

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
  model_uuid = var.juju_model_uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.smtp_legacy
  }

  application {
    name     = module.smtp_integrator[0].app_name
    endpoint = module.smtp_integrator[0].endpoints.smtp_legacy
  }
}

resource "juju_integration" "indico_local_saml_integrator" {
  model_uuid = var.juju_model_uuid

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
  model_uuid = var.juju_model_uuid

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
  model_uuid = var.juju_model_uuid

  application {
    name     = module.indico.app_name
    endpoint = module.indico.endpoints.redis_broker
  }

  application {
    name     = module.redis_broker[0].app_name
    endpoint = module.redis_broker[0].endpoints.redis
  }
}
