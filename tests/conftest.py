# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


def pytest_addoption(parser):
    parser.addoption("--indico-image", action="store")
    parser.addoption("--indico-nginx-image", action="store")


def pytest_generate_tests(metafunc):
    if "indico_image" in metafunc.fixturenames:
        metafunc.parametrize("indico_image", [metafunc.config.getoption("--indico-image")])
    if "indico_nginx_image" in metafunc.fixturenames:
        metafunc.parametrize(
            "indico_nginx_image", [metafunc.config.getoption("--indico-nginx-image")]
        )
