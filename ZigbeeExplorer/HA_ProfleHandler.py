'''
Created on 13 nov 2016

@author: RavalliAn
'''
from _struct import unpack

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

zonetype={
    0x0000: 'standard CIE',
    0x0028: 'fire sensor',
    0x002a: 'water sensor',
    0x002b: 'gas sensor' 
    }

manufacturers={0xffff: 'unknown'}

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
        frame_ctl = rfdata[0]
        print "Header: "
        print "\tFrame control:", str(bin(ord(frame_ctl))[2:]).zfill(8)
        if (ord(frame_ctl) == 16):
            #the command is manufacturer specific and also
            #the manufacturer code must be extracted 
            mcode, tx_seq, cmd_id= unpack('<HBB',rfdata[1:5])
            payload = rfdata[5:]
        else:
            tx_seq, cmd_id= unpack('<BB',rfdata[1:3])
            payload = rfdata[3:]
        print "\tTransaction Id: ", repr(tx_seq)
        print "\tCommand: ", repr(cmd_id)
        print "\tPayload: ", repr(payload)
        
        #format a base response
        response = {'cmd':'tx_explicit',
                    'dest_addr_long':addr64,
                    'dest_addr': addr16,
                    'src_endpoint': '\x00',
                    'dest_endpoint':'\x00',
                    'cluster': '', # cluster I want to deal with
                    'profile':'', # home automation profile
                    'data': ''
                    }
        
        # Discover Attributes: this command can be managed independently from the cluster
        if (cmd_id == '\x0d'):
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
                #print "    Attribute Set: ", str(bin(ord(attr_set))).zfill(12)
                try:
                    print datatypes[payload[i+2]]
                except:
                    print "I don't have an entry for datatype:", hex(ord(payload[i+2]))
                    #return
                finally:
                    i += 3
            return (node, None)
        
        if (zcls == 0x0000): # Under HA this is the 'Basic' Cluster
            print "...This cluster isn't handled yet"
            response = None
            pass
        elif (zcls == 0x0003): # 'identify' should make it flash a light or something 
            print "...This cluster isn't handled yet"
            response = None
            pass
        elif (zcls == 0x0004): # 'Groups'
            print "...This cluster isn't handled yet"
            response = None
            pass
        elif (zcls == 0x0005): # 'Scenes'  
            print "...This cluster isn't handled yet"
            response = None
            pass
        elif (zcls == 0x0500):
            print "IAS Zones cluster"
            response['cluster'] = '\x05' + '\x00'#'{:#06x}'.format(zcls)
            response = self.IASZone_handler(tx_seq, cmd_id, payload, response)
        elif (zcls == 0x0008): # 'Level'  
            response = None
            pass
        else:
            print("Haven't implemented this yet")
            response = None
        return node, response
    
    def IASZone_handler(self, txid, cmd, cmd_data, res):
        if (cmd==0b01):
            print "Enrollment Request"
            zt=(ord(cmd_data[1])<<8) + ord(cmd_data[0])
            m=(ord(cmd_data[3])<<8) + ord(cmd_data[2])
            print "command data report: " + zonetype[zt] + " by "  + manufacturers[m]
            res['dest_endpoint'] = 'x01' #TODO: end points should be selected from the node
            res['profile'] = '\x04\x01'
            '''
            RF data: 
                11 frame id
                -- seq
                00 cmd: enrole response
                00 status: success
                00 zone id
                '''
            res['data'] = '\x11' + chr(txid) + 'x00' + 'x00' + 'x00'
        elif(cmd=='\x00'):
            print "IAS Zone status change"
        else:
            print "Unrxpected Command"
            res = None
        return res





        