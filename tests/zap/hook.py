# pylint: skip-file
import logging


def zap_started(zap, target):
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
    logging.info(f"script.listEngines: {zap.script.list_engines}")
    logging.info(f"script.listScripts: {zap.script.list_scripts}")
