# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "app_names" {
  description = "Partial overrides for application names."
  type        = map(string)
  default     = {}

  validation {
    condition = length(
      setsubtract(keys(var.app_names), [
        "indico",
        "s3_integrator_media",
        "nginx_ingress_integrator",
        "local_postgresql",
        "redis_cache",
        "redis_broker"
      ])
    ) == 0

    error_message = "The keys in var.app_names must be one or more of: indico, s3_integrator_backup, s3_integrator_media, local_postgresql, nginx_ingress_integrator and redis_k8s."
  }
}

variable "channels" {
  description = "Partial overrides for charm channels. Keys follow same name as the variable enable."
  type        = map(string)
  default     = {}
}

variable "config_lego" {
  description = "Configuration for the Lego charm."
  type        = map(string)

  default = {
    "email" : "is-admin@canonical.com",
    "plugin" : "httpreq",
  }
}

variable "config_model" {
  description = "Configuration for the juju model."
  type        = map(string)
  default = {
    juju-http-proxy  = "" # override or set via locals
    juju-https-proxy = "" # override or set via locals
    juju-no-proxy    = "127.0.0.1,localhost,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.canonical.com,.launchpad.net,.internal,.jujucharms.com,.ubuntu.com"
  }
}

variable "config_nginx_ingress_integrator" {
  description = "Configuration for the nginx ingress integrator charm."
  type        = map(string)
  default = {
    max-body-size    = "21"
    service-hostname = "" # override or set via locals
  }
}

variable "config_s3_integrator_media" {
  description = "Configuration for the s3 integrator media charm."
  type        = map(string)
  default = {
    bucket       = "prod-indico-k8s-live-media"
    endpoint     = "https://radosgw.ps6.canonical.com"
    path         = "indico-media"
    region       = "prodstack6"
    s3-uri-style = "path"
  }
}

variable "config_local_saml_integrator" {
  description = "Configuration for the local saml integrator charm."
  type        = map(string)
  default     = {}
}

variable "config_local_postgresql" {
  description = "Configuration for the local postgresql charm."
  type        = map(string)
  default     = {}
}

variable "config_smtp_integrator" {
  description = "Configuration for the smtp integrator charm."
  type        = map(string)
  default = {
    auth_type          = "plain"
    transport_security = "tls"
    host               = "smtp-services.canonical.com"
    port               = "465"
    user               = ""
    password           = "" # override or set via locals
  }
}

variable "config_indico" {
  description = "Configuration for the indico charm."
  type        = map(string)

  default = {
    indico_external_plugins = "git+https://github.com/canonical/canonical-indico-themes.git@854e1d814db1ccb350d8d7413dd4156154802d3f,git+https://github.com/canonical/indico-plugin-event-countdown.git@5303299107db010ccdf6fdc42ca8aa930dfa433b,https://github.com/canonical/flask-multipass-saml-groups/releases/download/1.2.2/flask_multipass_saml_groups-1.2.2-py3-none-any.whl,https://github.com/canonical/canonical-indico-personal-agenda/releases/download/v2.0.0/indico_plugin_personal_agenda-2.0.0-py3-none-any.whl"
  }
}

variable "constraints" {
  description = "Constraints for each application."
  type        = map(string)
  default = {
    indico = "arch=amd64"
  }
}

variable "credentials" {
  description = "Static credentials map for various services."
  type        = map(string)
  default = {
    s3_access_key         = ""
    s3_secret_key         = ""
    lego_httpreq_username = ""
    lego_httpreq_password = ""
  }
  validation {
    condition = length(
      setsubtract(keys(var.credentials), [
        "s3_access_key",
        "s3_secret_key",
        "lego_httpreq_username",
        "lego_httpreq_password",
      ])
    ) == 0

    error_message = "The keys in var.credentials must be one or more of: s3_access_key, s3_secret_key, lego_httpreq_username, lego_httpreq_password."
  }
}

variable "enable" {
  description = "A map to enable or disable various components."
  type        = map(bool)
  default     = {}
  validation {
    condition = length(
      setsubtract(keys(var.enable), [
        "lego",
        "nginx_ingress_integrator",
        "local_postgresql",
        "local_saml_integrator",
        "redis_cache",
        "redis_broker",
        "s3_integrator_media",
        "smtp_integrator"
      ])
    ) == 0

    error_message = "The keys in var.enable must be one or more of: lego, nginx_ingress_integrator, local_postgresql, local_saml_integrator, maubot, redis_k8s, s3_integrator_backup, s3_integrator_media, smtp_integrator."
  }
}

variable "hostname" {
  description = "Matrix server URL."
  type        = string
  default     = "chat-server-live.ubuntu.com"
}

variable "integrate_offers" {
  description = "Partial overrides for integrating specific offers."
  type        = map(bool)
  default     = {}
  validation {
    condition = length(
      setsubtract(keys(var.integrate_offers), [
        "postgresql",
        "prometheus",
        "grafana",
        "saml_integrator"
      ])
    ) == 0

    error_message = "The keys in var.integrate_offers must be one or more of: postgresql, prometheus, grafana, saml_integrator."
  }
}

variable "lego_secret" {
  description = "Lego secret config."
  type = object({
    name  = string
    value = map(any)
  })

  default = {
    name = "indico-lego-credentials"
    value = {
      httpreq-endpoint            = "https://lego-certs.canonical.com"
      httpreq-username            = ""
      httpreq-password            = ""
      httpreq-propagation-timeout = 600
    }
  }
}

variable "model" {
  description = "Partial overrides for the model configuration."
  type        = map(string)
  default     = {}
}

variable "offer_urls" {
  description = "Partial overrides for external offer URLs."
  type        = map(string)
  default     = {}
  validation {
    condition = length(
      setsubtract(keys(var.offer_urls), [
        "postgresql",
        "prometheus",
        "grafana",
        "saml_integrator"
      ])
    ) == 0

    error_message = "The keys in var.offer_urls must be one or more of: postgresql, prometheus, grafana, saml_integrator."
  }

}

variable "revisions" {
  description = "Partial overrides for charm revisions. Keys follow same name as the variable enable."
  type        = map(number)
  default     = {}
}

variable "units" {
  description = "Partial overrides for unit counts. Only indico for now."
  type        = map(number)
  default     = {}
}
