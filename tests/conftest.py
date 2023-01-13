# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for WordPress charm tests."""


def pytest_addoption(parser):
    """Fixtures for WordPress charm tests."""
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")
