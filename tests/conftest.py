# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


def pytest_addoption(parser):
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")
    parser.addoption("--nginx-prometheus-exporter-image", action="store")
