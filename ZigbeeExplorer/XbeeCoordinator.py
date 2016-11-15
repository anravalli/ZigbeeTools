'''
Created on 13 nov 2016

@author: RavalliAn
'''
from xbee import ZigBee
from xbee.helpers import dispatch

from HA_ProfleHandler import HA_ProfileHandler
from ZDO_Handler import ZDO_Handler

import logging

import sys, traceback
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
    
    ha_handler = 0
    zdo_handler = 0

    def __init__(self, ser ):
        '''
        Constructor
        '''
        super(ser, callback=self._dispatcher)
        #read current config
        self._read_cofig()
        #check if config is coerent with HA profile
        
        self.ha_handler = HA_ProfileHandler()
        self.zdo_handler = ZDO_Handler()
        
        
    def _dev_read_cfg(self):
        self.send('at',
            command = 'ID'
        )
        
    def _dispatcher(self, data):
        '''
        here we receive and dispatch a received message
        '''
        if (data['id'] == 'rx_explicit'):
            print "RF Explicit received: dumping..."
            self._dump_rx_msg(data)
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
            print "field: ", field, "value: ",
            for b in msg[field]:
                print "{0:02x}".format(ord(b)),
            if (field =='id'):
                print "({})".format(msg[field]),
            print

        
# this is a call back function.  When a message
# comes in this function will get the data
    def rx_explicit_handler(self, data):
        try:
            switchLongAddr = data['source_addr_long']
            switchShortAddr = data['source_addr']
            print "RF Explicit (" + repr(data['cluster']) + ")"
            #printData(data)
            clusterId = (ord(data['cluster'][0])*256) + ord(data['cluster'][1])
            #print 'Cluster ID:', hex(ord(data['cluster'][0])), hex(ord(data['cluster'][1]))
            #print 'Cluster ID:', hex(clusterId),
            #print "profile id:", repr(data['profile'])
            if (data['profile']=='\x01\x04'): # Home Automation Profile
                self.ha_handler.handle(clusterId, data['rf_data'])
            elif (data['profile']=='\x00\x00'): # The General Profile
                print "nothing"
            else:
                print ("Unimplemented Profile ID")
        except:
            print "I didn't expect this error:", sys.exc_info()[0]
            traceback.print_exc()
        