#!/bin/sh
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
# Indico startup wrapper.
#
# Runs before every Indico Pebble service (web, worker, scheduler) and:
#   1. installs any extra plugins listed in $FLASK_EXTERNAL_PLUGINS (charm config)
#      into a writable per-user plugin directory;
#   2. exposes that directory on PYTHONPATH;
#   3. points Indico at the bundled `/srv/indico/indico.conf`;
#   4. execs the real service command passed as positional args.
#
# Concurrent service starts are serialized with `flock` so the three
# services (web/worker/scheduler) can never race the same `pip install`.
#
# Plugins are installed with `pip install --user` (PYTHONUSERBASE set to the
# plugin dir) rather than `--target`, so packages already baked into the image
# (indico itself and its dependency tree) are reused instead of being
# re-downloaded/re-compiled. An `indico==` constraint pins the Indico version
# so a plugin can never drag in a different Indico release.
#
# `--no-deps` is used because the Canonical Indico plugins are designed to
# layer on top of the already-installed Indico dependency tree; some pin a
# slightly different transitive dependency than Indico itself (e.g.
# flask-multipass-saml-groups pins flask-multipass==0.11 while indico pins
# ==0.11.2), which makes a full-resolution `pip install` fail with a version
# conflict. Installing --no-deps reuses the baked deps and matches how these
# plugins were previously baked into the rock at build time.
#
# `--break-system-packages` is required because the rock base (ubuntu@24.04)
# ships an externally-managed (PEP 668) Python; without it `pip install --user`
# aborts. We only ever write into the per-user plugin dir, never system files.

set -eu

PLUGIN_DIR="${PLUGIN_DIR:-/srv/indico/plugins}"
LOCK_FILE="${PLUGIN_DIR}/.install.lock"
STATE_FILE="${PLUGIN_DIR}/.installed"
# `pip install --user` with this base installs into
# ${PLUGIN_DIR}/lib/python3.12/site-packages.
PLUGIN_SITE="${PLUGIN_DIR}/lib/python3.12/site-packages"

export PYTHONUSERBASE="${PLUGIN_DIR}"

mkdir -p "${PLUGIN_SITE}"

if [ -n "${FLASK_EXTERNAL_PLUGINS:-}" ]; then
    # indico-operator format is comma-separated; pip wants space-separated.
    EXTRA_PLUGINS=$(printf '%s' "${FLASK_EXTERNAL_PLUGINS}" | tr ',' ' ')
    PIP_INDEX_URL="${FLASK_PIP_INDEX_URL:-}"
    # Only reinstall when the requested plugin set changes.
    REQUESTED_HASH=$(printf '%s\n%s\n' "${EXTRA_PLUGINS}" "${PIP_INDEX_URL:-}" | sha256sum | cut -d' ' -f1)
    INSTALLED_HASH=$(cat "${STATE_FILE}" 2>/dev/null || echo "")

    if [ "${REQUESTED_HASH}" != "${INSTALLED_HASH}" ]; then
        (
            flock -x 9
            CURRENT_HASH=$(cat "${STATE_FILE}" 2>/dev/null || echo "")
            if [ "${REQUESTED_HASH}" != "${CURRENT_HASH}" ]; then
                PIP_OPTS=""
                if [ -n "${PIP_INDEX_URL:-}" ]; then
                    PIP_OPTS="--index-url ${PIP_INDEX_URL}"
                fi
                # Pin the installed Indico version so plugins reuse it.
                CONSTRAINTS="${PLUGIN_DIR}/.constraints.txt"
                python3 -m pip freeze 2>/dev/null | grep '^indico==' > "${CONSTRAINTS}" || true
                # shellcheck disable=SC2086
                python3 -m pip install --no-cache-dir --user --upgrade \
                    --no-deps --break-system-packages \
                    -c "${CONSTRAINTS}" ${PIP_OPTS} ${EXTRA_PLUGINS}
                echo "${REQUESTED_HASH}" > "${STATE_FILE}"
            fi
        ) 9>"${LOCK_FILE}"
    fi
fi

export PYTHONPATH="${PLUGIN_SITE}${PYTHONPATH:+:${PYTHONPATH}}"
export INDICO_CONFIG="${INDICO_CONFIG:-/srv/indico/indico.conf}"

exec "$@"
