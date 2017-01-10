
import sys, traceback, threading
from xbee.base import ThreadQuitException
import time

class Monitor(threading.Thread):
    __monitor_on = False
    __monitor_cbk = 0
    __lock = 0
    __node = 0
    __terminate = False
    
    def __init__(self, monitor, node ):
        print "Init monitor loop"
        super(Monitor, self).__init__()
        self.__monitor_cbk = monitor
        self.__lock = threading.Lock()
        self.__node = node
        
        __terminate = False
        self.start()
        
    def run(self):
        print "Monitor running..."
        while True:
            try:
                if self.__monitor_on and not self.__terminate:
                    self.__monitor()
                else:
                    time.sleep(.5)
            except ThreadQuitException:
                # Expected termination of thread due to self.halt()
                break
            except Exception as e:
                # Unexpected thread quit.
                print "Catch exception: ", e
                print "...", sys.exc_info()[0]
                traceback.print_exc()
                break
    
    def __monitor(self):
        if self.__terminate:
            raise ThreadQuitException
        self.__monitor_cbk(self.__node)

    def startMonitor(self):
        self.__lock.acquire()
        print "Starting monitor on node: ", self.__node
        self.__monitor_on = True
        self.__lock.release()
        
    def stopMonitor(self):
        self.__lock.acquire()
        self.__monitor_on = False
        self.__lock.release()
    
    def halt(self):
        """
        halt: None -> None
        
        If this instance has a separate thread running, it will be
        halted. This method will wait until the thread has cleaned
        up before returning.
        """
        if self.__monitor:
            self.__terminate = True
            self.join()
        

class Cluster(object):
    
    cls_attributes = []
    
    
    def __init__(self):
        print "ciao"

class EndPoint(object):
    
    ep_type = "general"
    ep_id = None
    ep_device_id = None
    ep_zb_profile = None
    ep_clusters = []
    
    
        
    def __init__(self):
        print ""
        
class ZdoEndPoint(object):
    
    zdo_descriptors = []

class Node(object):
    
    nd_end_points = []
    nd_monitor = None
    
    ep_lock = threading.Lock
    
    def __init__(self):
        print ""
    