#!/bin/sh
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
# Idempotent Indico database bootstrap + migration entrypoint.
#
# `paas-charm` invokes this script on every unit. It is routed through
# `start-indico.sh` so that `INDICO_CONFIG` (and the runtime plugin paths) are
# exported exactly as they are for the web/worker/scheduler services; without
# it Indico cannot locate its config and therefore the database URI.
#
# Both `indico db prepare` (which creates the schema only when empty) and
# `indico db upgrade` are safe to run repeatedly.
set -eu

# `indico db prepare` initialises the schema but aborts with a non-zero exit
# code when the database is not empty (e.g. on charm upgrades / restarts).
# Run it only for a fresh database; otherwise fall through to `db upgrade`
# which is always safe to run repeatedly.
exec /srv/indico/start-indico.sh sh -ec '
if indico db prepare; then
    echo "Fresh database prepared."
else
    echo "Database already initialised; running upgrade."
fi
indico db upgrade
# Enabled plugins ship their own SQLAlchemy models in dedicated schemas
# (e.g. personal_agenda, custom_profile_fields, saml_groups). Their tables are
# NOT created by the core "db prepare"/"db upgrade"; without this step a logged
# in user hits "relation \"plugin_*\" does not exist" errors. Safe to run
# repeatedly and skips plugins that have no migrations folder.
indico db --all-plugins upgrade
'
