# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption("--charm-file", action="store")
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")
    parser.addoption("--saml-email", action="store")
    parser.addoption("--saml-password", action="store")
