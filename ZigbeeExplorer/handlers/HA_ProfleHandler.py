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
  along with ZigbeeTools; see the file COPYING.  If not, see
  <http://www.gnu.org/licenses/>.
  
'''

'''
Created on 13 nov 2016

@author: RavalliAn
'''
from _struct import unpack, pack
from utils.Utils import *

class HA_Exception(Exception):
    def __init__(self, err_msg):
        super(HA_Exception, self).__init__(err_msg)
        
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
        print "\tFrame control:", printableOctet(frame_ctl)
        
        if (ord(frame_ctl) & 0b00000100):
            #the command is manufacturer specific and also
            #the manufacturer code must be extracted 
            mcode, tx_seq, cmd_id, = unpack('<HBB',rfdata[1:5])
            payload = rfdata[5:]
        else:
            tx_seq, cmd_id, = unpack('<BB',rfdata[1:3])
            payload = rfdata[3:]
            
        print "\tTransaction Id: ", printableByte(tx_seq)
        print "\tCommand: ", printableByte(cmd_id)
        print "\tPayload: ", binDump(payload)

        #format a base response
        response = {'cmd':'tx_explicit',
                    'dest_addr_long':addr64,
                    'dest_addr': addr16,
                    'src_endpoint': '\xaa',
                    'dest_endpoint':'\x00',
                    'cluster': '', # cluster I want to deal with
                    'profile':'', # home automation profile
                    'data': ''
                    }
        
        # Discover Attributes: this command can be managed independently from the cluster
        if(ord(frame_ctl) & 0b00000001):
            print "cluster private command"
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
                response['cluster'] = pack('>H', zcls)
                response = self.IASZone_handler(tx_seq, cmd_id, payload, response, node)
            elif (zcls == 0x0008): # 'Level'  
                response = None
                pass
            else:
                print("Haven't implemented this yet")
                response = None
        else:
            print "profile wide command "
            (node, response) = self.genericCmdHandler(tx_seq, zcls, cmd_id, payload, node, response)
            
        
        return node, response
    
    def IASZone_handler(self, txid, cmd, cmd_data, res, node):
        if (cmd==0b01):
            print "------------- Enrollment Request ----------------------"
            zt=(ord(cmd_data[1])<<8) + ord(cmd_data[0])
            m=(ord(cmd_data[3])<<8) + ord(cmd_data[2])
            print "command data report: " + zonetype[zt] + " by "  + manufacturers[m]
            res['dest_endpoint'] = '\x01' #TODO: end points should be selected from the node
            res['profile'] = '\x01\x04'
            #bit fields: 000: reserved, 1: no def res, 0: client->server, 0: no private ext, 01: cls specific
            frm_type = 0b00000001
            cmd = '\x00' #enroll response
            er_st = '\x00' #enroll succeeded
            zone_id = '\x01' #use a well recognizable ID
            res['data'] = chr(frm_type) + chr(txid) + cmd + er_st + zone_id
            print "*** node is " + binDump(node['nwk_addr']) + "***"
            node['enrolled'] = True
        elif(cmd=='\x00'):
            print "IAS Zone status change: ", binDump(cmd_data)
        else:
            print "Unexpected Command"
            res = None
        return res

    def genericCmdHandler(self, tx_seq, zcls, cmd_id, cmd_data, node, response):
        if (cmd_id == 0x0d):
            print "-------------------------------------------------------"
            print "Discover attributes response"
            if (cmd_data[0] == '\x01'):
                print "All attributes returned"
            else:
                print "Didn't get all the attributes on one try"
            i = 1
            if (len(cmd_data) == 1): # no actual attributes returned
                print "No attributes"
                return
            attr_list = []
            while (i < len(cmd_data)-1):
                attr_id = [cmd_data[i+1], cmd_data[i]]
                a_type = cmd_data[i+2]
                attr = {'attr_id': attr_id, 'type':a_type}
                attr_list.append(attr)
                print "    Attribute = ", str(bin(ord(attr_id[0]))[2:]).zfill(8),str(bin(ord(attr_id[1]))[2:]).zfill(8),
                try:
                    print datatypes[a_type]['name']
                except:
                    print "I don't have an entry for datatype:", hex(ord(cmd_data[i+2]))
                    #return
                finally:
                    i += 3
            print "-------------------------------------------------------"
            for cls in node['clusters']:
                c, = unpack('>H',cls['cls_id'])
                #print "cluster: %s == %s" %(c, zcls)
                if c == zcls:
                    cls['attributes'] = attr_list
                    break
            return (node, None)
        elif (cmd_id == 0x01):
            print "Read Attribute: ", binDump(cmd_data)
            i = 0 #len(cmd_data)
            #print "data len: ", len(cmd_data)
            while (i < len(cmd_data)):
                #attr_id, status, = unpack('<HB',cmd_data[i:i+3])
                attr_id, status, = unpack('<HB',cmd_data[i:i+3])
                print "\tAttribute: ", binDump(pack('>H',attr_id))
                print "\tStatus: ", binDump(pack('>B',status))
                i+=3
                if(status==0x00):
                    dtype=cmd_data[i]
                    i+=1
                    if (dtype == '\x42'):
                        dlen=ord(cmd_data[i])
                        i+=1
                    else:
                        dlen=datatypes[dtype]['len']
                    #print "attr data len: ", dlen
                    attr_data = []
                    offset=i+dlen
                    while (i<offset):
                        # print i, dlen, i+dlen, i<i+dlen
                        attr_data.append(cmd_data[i])
                        i+=1
                    if (dtype == '\x42'):
                        print "\tAttribute data: ", attr_data
                    else:
                        if(dlen>1):
                            attr_data = swpByteOrder(attr_data)
                        print "\tAttribute data: ", binDump(attr_data)
                    print "\t\ttype: ", datatypes[dtype]['name']
            return (node, None)
        else:
            print ("No command matched")
            raise HA_Exception("No command matched")
            #return (node, None)
        