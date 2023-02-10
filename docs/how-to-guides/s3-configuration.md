# S3 configuration

An S3 bucket can be leveraged to serve the static content uploaded to Indico, potentially improving performance. Moreover, it is required when scaling the charm to serve the uploaded files. To configure it to set the appropriate connection parameters in `s3_storage` for your existing bucket `juju config [charm_name] s3_storage=[value]`.

The configuration option `s3_storage` accepts a comma separated list of parameters as in 's3:bucket=my-indico-test-bucket,access_key=12345,secret_key=topsecret'. More details can be found [in Indico's storage S3 documentation](https://github.com/indico/indico-plugins/blob/master/storage_s3/README.md#available-config-options).

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
