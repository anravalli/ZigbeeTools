'''
Created on 13 nov 2016

@author: RavalliAn
'''
from _struct import unpack

class HA_ProfileHandler(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    
    def handle(self, zcls, node, rfdata):
        addr64 = node['ieee_addr']
        addr16 = node['nwk_addr']
        print "Header: "
        print "\tFrame control:", str(bin(ord(rfdata[0]))[2:]).zfill(8)
        print "\tTransaction Id: ", repr(rfdata[1])
        print "\tCommand: ", hex(ord(rfdata[2]))
        if (rfdata[0] == '\x00'): # was it successful?
            #should have a bit check to see if manufacturer data is here
            cCommand = rfdata[2]
            print "Cluster command: ", hex(ord(cCommand))
        else:
            cCommand = rfdata[2]
            print "Cluster command failed"
            #return
        # grab the payload data to make it easier to work with
        payload = rfdata[3:] #from index 3 on is the payload for the command
        datatypes={'\x00':'no data',
            '\x10':'boolean',
            '\x18':'8 bit bitmap',
            '\x20':'unsigned 8 bit integer',
            '\x21':'unsigned 24 bit integer',
            '\x30':'8 bit enumeration',
            '\x42':'character string',
            '\xf0': 'IEEE address',
            '\x31':'16-bit enumeration',
            '\x19':'16-bit bitmap'}
        #print "Raw payload:",repr(payload)
        # handle these first commands in a general way
        if (cCommand == '\x0d'): # Discover Attributes
            # This tells you all the attributes for a particular cluster
            # and their datatypes
            print "Discover attributes response (zcls: ",zcls,")"
            if (payload[0] == '\x01'):
                print "All attributes returned"
            else:
                print "Didn't get all the attributes on one try"
            i = 1
            if (len(payload) == 1): # no actual attributes returned
                print "No attributes"
                return
            while (i < len(payload)-1):
                #attr = hex(ord(payload[i+1])) , hex(ord(payload[i]))
                #attr_set = payload[i+1] + (payload[i] >> 4)
                print "    Attribute = ", str(bin(ord(payload[i+1]))[2:]).zfill(8),str(bin(ord(payload[i]))[2:]).zfill(8),
                #print "        attribute set: ", str(bin(ord(attr_set))).zfill(12)
                try:
                    print datatypes[payload[i+2]]
                    
                except:
                    print "I don't have an entry for datatype:", hex(ord(payload[i+2]))
                    #return
                finally:
                    i += 3
            return
        
        if (zcls == 0x0000): # Under HA this is the 'Basic' Cluster
            pass
        elif (zcls == 0x0003): # 'identify' should make it flash a light or something 
            pass
        elif (zcls == 0x0004): # 'Groups'
            pass
        elif (zcls == 0x0005): # 'Scenes'  
            pass
        elif (zcls == 0x0500): # 'On/Off' this is for switching or checking on and off  
            print "IAS Zones cluster"
            if cCommand != None:
                print "...This command isn't handled yet"
            pass
        elif (zcls == 0x0008): # 'Level'  
            pass
        else:
            print("Haven't implemented this yet")