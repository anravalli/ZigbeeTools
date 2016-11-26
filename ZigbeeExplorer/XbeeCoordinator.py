'''
Created on 13 nov 2016

@author: RavalliAn
'''
from xbee import ZigBee
#from xbee.helpers import dispatch

from HA_ProfleHandler import HA_ProfileHandler
from ZDO_Handler import ZDO_Handler

import logging

import sys, traceback
from Utils import binDunp
#from __main__ import name

# This is the super secret home automation key that is needed to 
# implement the HA profile.
# KY parameter on XBee = 5a6967426565416c6c69616e63653039
# Have fun
class XbeeCoordinator(ZigBee):
    
    logging.basicConfig()
    '''
    store information about Xbee coordinator device
    '''
    #device = 0
    address_64 = '\x00\x00\x00\x00\x00\x00\x00\x00'
    address_16 = '\x00\x00'
    mac_address = 0
    #store here the xbee configuration
    c_dev_config = {
        
        }
    
    node_db_schema = {"entry" : 
                  ["IEEE_ADDR", "NWK_ADDR", {
                      "clusters":[
                          "profile_id", 
                          "cls_id"
                          ]}]}
        
    ha_handler = 0
    zdo_handler = 0
    node_db = [{"entry":0, "node":{"ieee_addr": "\x00\x00\x00\x00\x00\x00\x00\x00", "nwk_addr" : "\x00\x00", 
                                  "clusters": [{"profile_id":"\x04\x01", "cls_id":"\x00\x00"},
                                               {"profile_id":"\x04\x01", "cls_id":"\x00\x05"}]}}]

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
        #check if config is coerent with HA profile
        
        
    def _dev_read_cfg(self):
        print ""
        self.send('at',
            command = 'OI'
        )
        
    def _dispatcher(self, data):
        '''
        here we receive and dispatch a received message
        '''
        if (data['id'] == 'rx_explicit'):
            print "RF Explicit received:"
            #self._dump_rx_msg(data)
            self.rx_explicit_handler(data)
            
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
            pass
        else:
            print("some other type of packet")
            print(data)
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

    def addNewNode(self, node):
        print "Adding new node: ", self._getAsString(node['nwk_addr'])
        db_len = self.node_db.__len__()
        new_node = {'entry': db_len, 'node': node}
        self.node_db.append(new_node)
        #print "...with nwk_addr: ", self._getAsString(node['node']['nwk_addr'])
        
    def rx_explicit_handler(self, data):
        
        try:
            self._lock.acquire()
            print "RX Explicit from End Point: " + repr(data['source_endpoint']) + \
                ", Profile: " + repr(data['profile']) + \
                ", Cluster: " + repr(data['cluster'])
                
            node = self.getNodeFromAddress(data['source_addr_long'])
            if (node == None):
                print "New Node found"
                node = {'ieee_addr': data['source_addr_long'], 'nwk_addr': data['source_addr']}
                self.addNewNode(node)
            else:
                print "Node found in DB"
            
            clusterId = (ord(data['cluster'][0])*256) + ord(data['cluster'][1])
            if (data['profile']=='\x01\x04'): # Home Automation Profile
                print "HA profile found"
                node, res = self.ha_handler.handle(clusterId, node, data['rf_data'])
            elif (data['profile']=='\x00\x00'):
                print "ZDO profile found"
                node, res = self.zdo_handler.handle(clusterId, node, data['rf_data'])
            else:
                print ("Unimplemented Profile ID")
            if (res != None):
                self.send_response(res)
        except:
            print "I didn't expect this error:", sys.exc_info()[0]
            traceback.print_exc()
        finally:
            self._lock.release()
    
    def send_response(self, res):
        print "---- send response: ", binDunp(res['data'])
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
        
        
    def getNodeFromAddress(self, ieee_addr):
        try:
            for node in self.node_db:
                #print "Checking node with index: ", node['entry']
                node = node["node"]
                if (node["ieee_addr"]==ieee_addr):
                    return node
        except:
            print "exception"
            return None 
        return None
        