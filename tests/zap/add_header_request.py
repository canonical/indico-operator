headers = dict({"Host": "indico.local"});

def sendingRequest(msg, initiator, helper):
    for h in list(headers):
      msg.getRequestHeader().setHeader(h, headers[h]);

def responseReceived(msg, initiator, helper):
    pass;
