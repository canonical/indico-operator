# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption("--charm-file", action="store")
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="keep temporarily-created models",
    )
    parser.addoption(
        "--use-existing",
        action="store_true",
        default=False,
        help="use existing models and not created models",
    )
    parser.addoption(
        "--model",
        action="store",
        help="temporarily-created model name",
    )
    parser.addoption(
        "--indico-image",
        action="store",
        help="indico OCI rock image URI",
    )
    parser.addoption("--s3-address", action="store")
