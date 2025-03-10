# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.


# pylint: disable=missing-module-docstring,invalid-name,unused-argument
# linting rules disabled due to this file is defined by ZAP tool script template
def sendingRequest(msg, initiator, helper):  # noqa: N802
    """Sendingrequest is a name defined and expected by ZAP tool

    Args:
        msg (HttpMessage): all requests/responses sent/received by ZAP
        initiator (int): the component that initiated the request
        helper (HttpSender): returns the HttpSender instance used to send the request

    Returns:
        HttpMessage: returns HttpMessage updated
    """
    msg.setUserObject({"host": "events.staging.canonical.com"})
    return msg


def responseReceived(msg, initiator, helper):  # noqa: N802
    """Responsereceived is a name defined and expected by ZAP tool

    Args:
        msg (HttpMessage): all requests/responses sent/received by ZAP
        initiator (int): the component that initiated the request
        helper (HttpSender): returns the HttpSender instance used to send the request
    """
