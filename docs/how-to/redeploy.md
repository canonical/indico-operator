# How to redeploy Indico

This guide provides the necessary steps for migrating an existing Indico instance to a new charm instance.

## Migrate the database

Follow the instructions in [the charm migration documentation](https://charmhub.io/postgresql-k8s/docs/h-migrate-cluster-via-restore) to migrate the content of the Indico PostgreSQL database.

## Migrate files stored in S3

If your media files are stored in an S3 bucket, you have two options:

1. Provide the new Indico charm instance with the same credentials and connection information for the object storage. This allows the new instance to automatically access the existing files.
2. Use tools like [rclone](https://rclone.org) to copy files from the old
   storage bucket to a new bucket for the new deployment.

If the files are not stored in S3, they are not expected to persist across unit restartars or to be available in multiple units. However, it is still possible to copy them from to the new charm instance using [juju scp](https://juju.is/docs/juju/juju-scp).
