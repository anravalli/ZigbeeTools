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
        response = None
        
        frame_ctl = rfdata[0]
        print "Header: "
        print "\tFrame control:", str(bin(ord(frame_ctl))[2:]).zfill(8)
        if (frame_ctl & 0b00000001):
            #the command is manufacturer specific and 
            #the manufacturer code must be extracted also
            mcode, tx_seq, cmd_id= unpack('<HBB',rfdata[1:5])
            payload = rfdata[5:]
        else:
            tx_seq, cmd_id= unpack('<BB',rfdata[1:])
            payload = rfdata[3:]
        print "\tTransaction Id: ", repr(tx_seq)
        print "\tCommand: ", repr(cmd_id)
        print "\tPayload: ", repr(payload)
        
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
        
        if (cmd_id == '\x0d'): # Discover Attributes
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
            print "...This command isn't handled yet"
            pass
        elif (zcls == 0x0003): # 'identify' should make it flash a light or something 
            print "...This command isn't handled yet"
            pass
        elif (zcls == 0x0004): # 'Groups'
            print "...This command isn't handled yet"
            pass
        elif (zcls == 0x0005): # 'Scenes'  
            print "...This command isn't handled yet"
            pass
        elif (zcls == 0x0500):
            print "IAS Zones cluster"
            if cmd_id != None:
                print ""
            pass
        elif (zcls == 0x0008): # 'Level'  
            pass
        else:
            print("Haven't implemented this yet")
        return node, response