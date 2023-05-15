# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")
    parser.addoption("--saml-email", action="store")
    parser.addoption("--saml-password", action="store")
