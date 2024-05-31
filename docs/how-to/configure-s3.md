# How to configure S3

An S3 bucket can be leveraged to serve the static content uploaded to Indico, potentially improving performance. Moreover, it is required when scaling the charm to serve the uploaded files.

To configure Indico's S3 integration you'll have to deploy the [S3 Integrator charm](https://charmhub.io/s3-integrator/docs/tutorial-getting-started) and integrate it with Indico by running `juju integrate indico s3-integrator`.