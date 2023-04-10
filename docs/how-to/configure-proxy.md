# How to configure proxy

This charm supports several operations that require access to external resources, such as customization or plugins installation, so your environment may not be able to reach those URLs unless through a proxy. The proxy can be configured via two configuration options `http_proxy` for HTTP requests, and `https_proxy` for HTTPS request.

Assuming Indico is already up and running as `indico`, you'll need to run the following commands:
```
juju config indico http_proxy=http://squid.example:3128
juju config indico http_proxy=http://squid.example:3128
```

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
