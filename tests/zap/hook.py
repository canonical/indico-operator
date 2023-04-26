# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=missing-module-docstring,invalid-name,unused-argument
# linting rules disabled due to this file is defined by ZAP tool script template
import logging


def zap_started(zap, target):
    """Actions when starts

    Args:
        zap (ZAPv2): ZAPv2 instance
        target (string): Target being scanned
    """
    logging.info(
        zap.script.load(
            "Add Header Script",
            "httpsender",
            "python : jython",
            "/zap/wrk/tests/zap/add_header_request.py",
        )
    )
    logging.info(zap.script.enable("Add Header Script"))


def zap_pre_shutdown(zap):
    """Actions before shutdown

    Args:
        zap (ZAPv2): ZAPv2 instance
    Returns:
        None
    """
    logging.info("script.listEngines: %s", zap.script.list_engines)
    logging.info("script.listScripts: %s", zap.script.list_scripts)
