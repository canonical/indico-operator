output "applications" {
  description = "Applications deployed by the product."
  value = {
    lego                     = local.enable.lego ? module.lego : null
    nginx_ingress_integrator = local.enable.nginx_ingress_integrator ? module.nginx_ingress_integrator : null
    redis_cache              = local.enable.redis_cache ? module.redis_cache : null
    redis_broker             = local.enable.redis_broker ? module.redis_broker : null
    s3_integrator_media      = local.enable.s3_integrator_media ? module.s3_integrator_media : null
    smtp_integrator          = local.enable.smtp_integrator ? module.smtp_integrator : null
    local_saml_integrator    = local.enable.local_saml_integrator ? module.local_saml_integrator : null
    local_postgresql         = local.enable.local_postgresql ? module.local_postgresql : null
    indico                   = module.indico
  }
}

output "model_uuid" {
  value = juju_model.indico.uuid
}
