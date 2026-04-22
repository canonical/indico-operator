# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  app_names_defaults = {
    s3_integrator_media      = "media-s3-integrator"
    indico                   = "indico"
    redis_cache              = "redis-cache"
    redis_broker             = "redis-broker"
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

  config_s3_integrator_media = var.config_s3_integrator_media

  config_smtp_integrator = merge(
    var.config_smtp_integrator,
    {}
  )

  config_local_saml_integrator = merge(
    var.config_local_saml_integrator,
    {}
  )

  config_indico = merge(var.config_indico, {})

  credentials = merge(
    var.credentials, {}
  )

  revisions_defaults = {
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
  }

  revisions = merge(local.revisions_defaults, var.revisions)

  units_defaults = {
    indico = 1
  }

  units = merge(local.units_defaults, var.units)
}
