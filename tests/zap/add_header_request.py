# pylint: skip-file
def sendingRequest(msg, initiator, helper):  # noqa: N802
    msg.getRequestHeader().setHeader("Host", "indico.local")


def responseReceived(msg, initiator, helper):  # noqa: N802
    pass
