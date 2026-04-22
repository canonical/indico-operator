output "applications" {
  description = "Applications deployed by the product."
  value = {
    redis_cache              = module.redis_cache
    redis_broker             = module.redis_broker
    s3_integrator_media      = module.s3_integrator_media
    smtp_integrator          = module.smtp_integrator
    local_saml_integrator    = module.local_saml_integrator
    indico                   = module.indico
  }
}
