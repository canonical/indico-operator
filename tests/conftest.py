# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options."""
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")
