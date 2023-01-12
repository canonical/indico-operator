def zap_started(zap, target):
   print(zap.script.load('Add Header Script', 'httpsender', 'python : jython', '/zap/wrk/tests/zap/add_header_request.py'))
   print(zap.script.enable('Add Header Script'))

def zap_pre_shutdown(zap):
    print("script.listEngines")
    print(zap.script.list_engines)
    print()
    print("script.listScripts")
    print(zap.script.list_scripts)
