'''
  Copyright (C) 2016 Andrea Ravalli (anravalli@gmail.com)

  This Program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2, or (at your option)
  any later version.
 
  This Program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.
 
  You should have received a copy of the GNU General Public License
  along with Kodi; see the file COPYING.  If not, see
  <http://www.gnu.org/licenses/>.
  
'''

'''
@author: Andrea Ravalli 
Created on 13 nov 2016
'''

from xbee import ZigBee
from xbee.base import ThreadQuitException
#from xbee.helpers import dispatch

from handlers.HA_ProfleHandler import HA_ProfileHandler
from handlers.ZDO_Handler import ZDO_Handler

import logging
import time
import sys, traceback, threading
from utils.Utils import binDump
#from __main__ import name

class NodeMonitor(threading.Thread):
    __monitor_on = False
    __monitor_cbk = 0
    __lock = 0
    __node = 0
    __terminate = False
    
    def __init__(self, monitor, node ):
        print "Init monitor loop"
        super(NodeMonitor, self).__init__()
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
        
# This is the super secret home automation key that is needed to 
# implement the HA profile.
# KY parameter on XBee = 5a6967426565416c6c69616e63653039
# Have fun
class XbeeCoordinator(ZigBee):
    
    logging.basicConfig()
    '''
    Manage the Xbee device
    '''

#     node_db_schema = {"entry" : 
#                   ["IEEE_ADDR", "NWK_ADDR", {
#                       "clusters":[
#                           "profile_id", 
#                           "cls_id"
#                           ]}]}
        
#     node_db = [{"entry":0, "node":{"ieee_addr": "\x00\x00\x00\x00\x00\x00\x00\x00", "nwk_addr" : "\x00\x00", 
#                                   "clusters": [{"profile_id":"\x04\x01", "cls_id":"\x00\x00"},
#                                                {"profile_id":"\x04\x01", "cls_id":"\x00\x05"}]}}]
    node_db = []
    
    ha_handler = 0
    zdo_handler = 0
    monitor_func = 0
    #monitor   = 0
    
    def __init__(self, ser, lock ):
        '''
        Constructor
        '''
        self._lock=lock
        super(XbeeCoordinator, self).__init__(ser, callback=self._dispatcher)
        self.ha_handler = HA_ProfileHandler()
        self.zdo_handler = ZDO_Handler()
        
        #read current config
        self._dev_read_cfg()
        #check if config. is coherent with HA profile
            
    def _dev_read_cfg(self):
        print "Network Discovery"
        self.send('at',
            command = 'ND'
        )
        
    def _dispatcher(self, data):
        '''
        here we receive and dispatch a received message
        '''
        #print "Message received: ", binDump(data) 
        if (data['id'] == 'rx_explicit'):
            try:
                print "RF Explicit received"
                #self._dump_rx_msg(data)
                self.rx_explicit_handler(data)
            except Exception as e:
                print "\nException catched:"
                print e
                self._dump_rx_msg(data)
        elif (data['id'] == 'tx_status'):
            print "TX status received: dumping..."
            self._dump_rx_msg(data)
                  
        elif (data['id'] == 'at_response'):
            print "AT response received: dumping..."
            self._dump_rx_msg(data)
        
        elif (data['id'] == 'remote_at_response'):
            print "Remote AT responses received: dumping..."
            self._dump_rx_msg(data)
            
        elif (data['id'] == 'status'):
            print "Status received: dumping..."
            self._dump_rx_msg(data)
        elif(data['id'] == 'route_record_indicator'):
            print("Route Record Indicator")
            self._dump_rx_msg(data)
        else:
            print("Unmanaged frame type: dumping")
            self._dump_rx_msg(data)
            
    '''
        This routine will print the data received so you can follow along if necessary
    '''   
    def _dump_rx_msg(self, msg):
        for field in msg:
            print field, ": ",
            if (field =='id'):
                print "({})".format(msg[field])
                return
            for b in msg[field]:
                print "{0:02x}".format(ord(b)),
            print

    def _getAsString(self, attr):
        
        attr_str = []
        for c in attr:
            attr_str.append("{0:02x}".format(ord(c)))
            #print "debug: ", attr_str
        return attr_str
    
    def rx_explicit_handler(self, data):
        
        try:
            self._lock.acquire()
            print "RX Explicit from " + binDump(data['source_addr']) + \
                ", Profile: " + binDump(data['profile']) + \
                ", Cluster: " + binDump(data['cluster'])
            print "Raw data in message: " + binDump(data['rf_data'])
            
            node = self.getNodeFromAddress(data['source_addr_long'])
            if (node == None):
                print "New Node found"
                node = {'ieee_addr': data['source_addr_long'], 'nwk_addr': data['source_addr']}
                self.addNewNode(node)

            node['alive'] = True
            
            clusterId = (ord(data['cluster'][0])*256) + ord(data['cluster'][1])
            if (data['profile']=='\x01\x04'): # Home Automation Profile
                print "HA profile found"
                nodes, res = self.ha_handler.handle(clusterId, node, data['rf_data'])
            elif (data['profile']=='\x00\x00'):
                print "ZDO profile found"
                nodes, res = self.zdo_handler.handle(clusterId, node, data['rf_data'])
            else:
                print ("Unimplemented Profile ID")
            if (res != None):
                self.send_response(res)
            if (nodes != None):
                if (type(nodes) is list):
                    for n in nodes:
                        self.checkinNode(n)
                        #print "Node is: ", binDump(n['ieee_addr'])
                        self.setEnrollmentAndMonitor(n['ieee_addr'])
                else:
                    self.checkinNode(nodes)
                    self.setEnrollmentAndMonitor(nodes['ieee_addr'])
                    #print "Node is: ", nodes['nwk_addr']

        except:
            print "I didn't expect this error:", sys.exc_info()[0]
            traceback.print_exc()
        finally:
            self._lock.release()
    
        
    def send_response(self, res):
        print "---- send response: ", binDump(res['data'])
        self.send(res['cmd'],
                  dest_addr_long = res['dest_addr_long'],
                  dest_addr = res['dest_addr'],
                  src_endpoint = res['src_endpoint'],
                  dest_endpoint = res['dest_endpoint'],
                  cluster = res['cluster'],
                  profile = res['profile'],
                  data = res['data']
                  )
        print "---- response sent ---- "

    def setMonitorFunction(self, func):
        self._lock.acquire()
        self.monitor_func = func
        self._lock.release()
        
    def setEnrollmentAndMonitor(self, ieee):
        n = self.getNodeFromAddress(ieee)
        try: 
            print "setEnrollmentAndMonitor for ", binDump(n['nwk_addr'])
            #self._lock.acquire()
            print "...is enrolled?", n['enrolled']
            if n['enrolled'] and n['monitor'] == None:
                n['monitor'] = NodeMonitor(self.monitor, self.getNodeIdx(n['ieee_addr']))
                n['monitor'].startMonitor()
        except:
            print "I didn't expect this error:", sys.exc_info()[0]
            traceback.print_exc()
        finally:
            print "...enrolled..."
            #self._lock.release()
    '''
    Nodes Database access and manipulation functions
    '''
    
    def checkinNode(self, node):
        #print "debug -- ", node
        ret_node = self.getNodeFromAddress(node['ieee_addr'])
        if (ret_node == None):
            print "New Node found"
            self.addNewNode(node)
        elif ret_node['nwk_addr'] != node['nwk_addr']:
            print "Updating Node nwk_address from " + binDump(ret_node['nwk_addr']) + \
                " to " + node['nwk_addr']
            ret_node['nwk_addr'] = node['nwk_addr']
        
    def getNodeFromAddress(self, ieee_addr):
        print "Checking address: ", binDump(ieee_addr)
        try:
            for db_entry in self.node_db:
                #print "Checking node with index: ", node['entry']
                node = db_entry["node"]
                if (node["ieee_addr"]==ieee_addr):
                    print "...node found"
                    return node
        except:
            print "exception"
            return None 
        return None
    
    def addNewNode(self, node):
        print "Adding new node: ", self._getAsString(node['nwk_addr'])
        db_len = self.node_db.__len__()
        
        node['enrolled'] = False 
        node['alive'] = False
        node['monitor'] = None

        new_node = {'entry': db_len, 'node': node}

        #print "Node is enrolled?", new_node['node']['enrolled']
        self.node_db.append(new_node)
        #print "...with nwk_addr: ", self._getAsString(node['node']['nwk_addr'])
    
    def getNodeIdx(self, ieee_addr):
        print "Getting index for : ", binDump(ieee_addr)
        try:
            print "---- DB size: ", len(self.node_db)
            for i in range(len(self.node_db)):
                #node = self.node_db
                print "---- Index is: ", i
                if (self.node_db[i]['node']['ieee_addr']==ieee_addr):
                    print "returning index of: ", binDump(self.node_db[i]['node']['ieee_addr'])
                    print "Index is: ", i
                    return i
        except:
            print "I didn't expect this error:", sys.exc_info()[0]
            traceback.print_exc()
            return -2 #exception
        
        return -1 #not found
    
    def monitor(self, node_idx):
        print time.strftime("%A, %B, %d at %H:%M:%S"), " - Monitor started on node: ", node_idx
        counter = 0
        poll_count = 0
        poll = False
        time.sleep(30)
        while True:
            if poll:
                if poll_count < 10:
                    print ".",
                    self._lock.acquire()
                    self.monitor_func(node_idx)
                    self._lock.release()
                    poll_count += 1
                    time.sleep(1)
                else:
                    print "going to time.sleep!"
                    print time.strftime("%H:%M:%S"), "- sleep time is: ", self.node_db[node_idx]['timeout']
                    time.sleep(self.node_db[node_idx]['timeout'])
                    print time.strftime("%H:%M:%S"), "Wake up!!!"
                    poll_count = 0
                    self.node_db[node_idx]['node']['alive'] = False
            else:
                print "+",
                self._lock.acquire()
                self.monitor_func(node_idx)
                self._lock.release()
                time.sleep(1)
                counter += 1
                
            if self.node_db[node_idx]['node']['alive'] :
                print time.strftime("%H:%M:%S"), "- received zone status answer" 
                if not poll:
                    print "first time"
                    self.node_db[node_idx]['last_msg'] = time.strftime("%H:%M:%S")
                    if counter > 5:
                        self.node_db[node_idx]['timeout'] = counter-5
                    else:
                        self.node_db[node_idx]['timeout'] = counter
                    print time.strftime("%H:%M:%S"), "+ sleep time is: ", self.node_db[node_idx]['timeout']
                    time.sleep(self.node_db[node_idx]['timeout'])
                    print time.strftime("%H:%M:%S"), "Wake up!!!"
                    counter = 0
                    poll = True
                    self.node_db[node_idx]['node']['alive'] = False
        
    
    
