import threading
import time
#Memory usage
#import psutil
import os

def setInterval(func, sec, process, mylist):
    def inner():
        while function.isAlive():
            func(process, mylist)
            time.sleep(sec)
    function = type("setInterval", (), {}) # not really a function I guess
    function.isAlive = lambda: function.vars["isAlive"]
    function.vars = {"isAlive": True}
    function.cancel = lambda: function.vars.update({"isAlive": False})
    thread = threading.Timer(sec, inner)
    thread.setDaemon(True)
    thread.start()
    return function
    
def myfunc(process, mylist):
    mylist.append(process.memory_info().rss/1000000)
