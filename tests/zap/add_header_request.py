headers = dict({"Host": "indico.local"})


def sendingRequest(msg, initiator, helper):  # noqa: N802
    for h in list(headers):
        msg.getRequestHeader().setHeader(h, headers[h])


def responseReceived(msg, initiator, helper):  # noqa: N802
    pass
