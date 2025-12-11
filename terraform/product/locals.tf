# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  app_names_defaults = {
    s3_integrator_media      = "media-s3-integrator"
    indico                   = "indico"
    redis_cache              = "redis-cache"
    redis_broker             = "redis-broker"
    nginx_ingress_integrator = "nginx-ingress-integrator"
    local_postgresql         = "postgresql-k8s"
  }
  app_names = merge(local.app_names_defaults, var.app_names)

  channels_defaults = {
    lego                     = "4/stable"
    nginx_ingress_integrator = "latest/edge"
    redis_cache              = "latest/edge"
    redis_broker             = "latest/edge"
    s3_integrator_media      = "latest/edge"
    smtp_integrator          = "latest/edge"
    indico                   = "latest/edge"
    local_postgresql         = "14/edge"
    local_saml_integrator    = "latest/edge"
  }

  channels = merge(local.channels_defaults, var.channels)

  config_lego = merge(var.config_lego, {
    "plugin-config-secret-id" : (local.enable.nginx_ingress_integrator && local.enable.lego) ? juju_secret.lego_credentials[0].secret_id : null,
  })

  config_model = merge(
    var.config_model,
    {}
  )

  config_nginx_ingress_integrator = merge(
    var.config_nginx_ingress_integrator,
    {
      service-hostname = var.hostname
    }
  )

  config_s3_integrator_media = var.config_s3_integrator_media

  config_smtp_integrator = merge(
    var.config_smtp_integrator,
    {}
  )

  config_local_saml_integrator = merge(
    var.config_local_saml_integrator,
    {}
  )

  config_local_postgresql = merge(
    var.config_local_postgresql,
    {}
  )

  config_indico = merge(var.config_indico, {})

  credentials = merge(
    var.credentials, {}
  )

  enable_defaults = {
    lego                     = false
    local_saml_integrator    = false
    local_postgresql         = false
    nginx_ingress_integrator = false
    redis_cache              = false
    redis_broker             = false
    s3_integrator_media      = false
    smtp_integrator          = false
  }

  enable = merge(local.enable_defaults, var.enable)

  integrate_offers_defaults = {
    grafana         = false
    postgresql      = true
    prometheus      = false
    saml_integrator = false
  }

  integrate_offers = merge(local.integrate_offers_defaults, var.integrate_offers)

  model_defaults = {
    constraints = "root-disk-source=volume"
  }

  model = merge(local.model_defaults, var.model)

  offer_urls_defaults = {}
  offer_urls          = merge(local.offer_urls_defaults, var.offer_urls)

  revisions_defaults = {
    lego = 61
    # renovate: depName="nginx-ingress-integrator"
    nginx_ingress_integrator = 81
    # renovate: depName="redis-k8s"
    redis_cache = 25
    # renovate: depName="redis-k8s"
    redis_broker = 25
    # renovate: depName="s3-integrator"
    s3_integrator_media = 13
    # renovate: depName="smtp-integrator"
    smtp_integrator = 15
    # renovate: depName="indico"
    indico = 620
    # renovate: depName="saml-integrator"
    local_saml_integrator = 102
    # renovate: depName="postgresql-k8s"
    local_postgresql = 665
  }

  revisions = merge(local.revisions_defaults, var.revisions)

  units_defaults = {
    indico = 1
  }

  units = merge(local.units_defaults, var.units)

  lego_secret = {
    name = var.lego_secret.name
    value = merge(
      var.lego_secret.value,
      {
        httpreq-username = local.credentials.lego_httpreq_username
        httpreq-password = local.credentials.lego_httpreq_password
      }
    )
  }
}
