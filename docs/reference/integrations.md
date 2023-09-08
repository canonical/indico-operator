# Integrations

### db

_Interface_: pgsql  
_Supported charms_: [postgresql-k8s](https://charmhub.io/postgresql-k8s), [postgresql](https://charmhub.io/postgresql)

Database integration is a required relation for the indico charm to supply structured data
storage for Indico.

Example db integrate command: `juju integrate indico postgresql-k8s:db`

### redis

_Interface_: redis  
_Supported charms_: [redis-k8s](https://charmhub.io/redis-k8s)

Redis integration is a required relation for the indico charm to supply caching capabilities and
a message broker to interface with Celery. As such, two instances are needed, `redis-cache` and 
`redis-broker`.

Example db integrate commands: `juju integrate redis-cache indico`, `juju integrate redis-broker indico`

### ingress

_Interface_: ingress  
_Supported charms_: [nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator)

Ingress manages external http/https access to services in a kubernetes cluster.
Ingress relation through [nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator)
charm enables additional `blog_hostname` and `use_nginx_ingress_modesec` configurations. Note that the
kubernetes cluster must already have an nginx ingress controller already deployed. Documentation to
enable ingress in microk8s can be found [here](https://microk8s.io/docs/addon-ingress).

Example ingress integrate command: `juju integrate wordpress-k8s nginx-ingress-integrator`

### metrics-endpoint

_Interface_: [prometheus_scrape](https://charmhub.io/interfaces/prometheus_scrape-v0)  
_Supported charms_: [prometheus-k8s](https://charmhub.io/prometheus-k8s)

Metrics-endpoint relation allows scraping the `/metrics` endpoint provided by apache-exporter sidecar
on port 9117, which provides apache metrics from apache’s `/server-status` route. This internal
apache’s `/server-status` route is not exposed and can only be accessed from within the same
Kubernetes pod. The metrics are exposed in the [open metrics format](https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md#data-model) and will only be scraped by Prometheus once the relation becomes active. For more
information about the metrics exposed, please refer to the apache-exporter [documentation](https://github.com/Lusitaniae/apache_exporter#collectors).

Metrics-endpoint integrate command: `juju integrate wordpress-k8s prometheus-k8s`

### grafana-dashboard

_Interface_: grafana-dashboard  
_Supported charms_: [grafana-k8s](https://charmhub.io/grafana-k8s)

Grafana-dashboard relation enables quick dashboard access already tailored to fit the needs of
operators to monitor the charm. The template for the Grafana dashboard for wordpress-k8s charm can
be found at `/src/grafana_dashboards/wordpress.json`. In Grafana UI, it can be found as “WordPress
Operator Overview” under the General section of the dashboard browser (`/dashboards`). Modifications
to the dashboard can be made but will not be persisted upon restart/redeployment of the charm.

Grafana-Prometheus integrate command: `juju integrate grafana-k8s:grafana-source prometheus-k8s:grafana-source`  
Grafana-dashboard integrate command: `juju integrate wordpress-k8s grafana-dashboard`

See more information in [Charm Architecture](https://charmhub.io/indico/docs/explanation-charm-architecture).
