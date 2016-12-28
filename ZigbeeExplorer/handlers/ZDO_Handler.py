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
Created on 13 nov 2016

@author: RavalliAn
'''
from struct import unpack, pack
from utils.Utils import *

class ZDO_Handler(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        print "ZDO Handler constructor"
        
    def handle(self, zcls, node, rfdata):
        addr64 = node['ieee_addr']
        addr16 = node['nwk_addr']
        response = None
        
        if (zcls == 0x0000):
            print ("Network (16-bit) Address Request")
            raise Exception("Unmanaged Message")
        elif (zcls == 0x0001):
            print ("IEEE (64-bit) Address Request")
            raise Exception("Unmanaged Message")
        elif (zcls == 0x0004):
            print("Simple Descriptor Request")
            raise Exception("Unmanaged Message")
        elif (zcls == 0x0013):
            # This is the device announce message.
            print 'Device Announce Message: ', binDump(rfdata)
            print "\n"
        elif (zcls == 0x8000):
            print("Network (16-bit) Address Response")
            childs = self.processChildTable(rfdata)
            print "Node "+ binDump(addr16) +" has " + len(childs) + " child:" 
            i=0
            for c in childs:
                print "child #"+i+": "+binDump(c['nwk_addr'])
                i+=1
        elif (zcls == 0x8001):
            print ("IEEE (64-bit) Address Response")
            childs = self.processChildTable(rfdata)
            if (childs != None):
                print "Node "+ binDump(addr16) +" has " + str(len(childs)) + " child:" 
                i=0
                for c in childs:
                    print "child #"+str(i)+": "+binDump(c['nwk_addr'])
                    i+=1
                
        elif (zcls == 0x8031):
            print "Neighbor Table Response"
            childs = self.processNeighborTable(node, rfdata)
            print "Node "+ binDump(addr16) +" has " + str(len(childs)) + " child:" 
            i=0
            for c in childs:
                print "child #"+str(i)+":"+binDump(c['nwk_addr'])
                i+=1
            node = childs
        elif (zcls == 0x8032):
            print "Route Record Response"
        elif (zcls == 0x8038):
            print("Management Network Update Request");
        elif (zcls == 0x8005):
            # this is the Active Endpoint Response This message tells you
            # what the device can do
            print 'Active Endpoint Response'
            if (ord(rfdata[1]) == 0): # this means success
                print "Active Endpoint reported back is: {0:02x}".format(ord(rfdata[5]))
            print("Now trying simple descriptor request on endpoint 01")
            print("---not implemented yet----")
            
        elif (zcls == 0x8004):
            print "simple descriptor response"
            try:
                #clustersFound = []
                r = rfdata
                if (ord(r[1]) == 0): # means success
                    #take apart the simple descriptor returned
                    endpoint, profileId, deviceId, version, inCount = \
                        unpack('<BHHBB',r[5:12])
                    node['device_id']=deviceId
                    print "    endpoint reported is: {0:02x}".format(endpoint)
                    print "    profile id:  {0:04x}".format(profileId)
                    print "    device id: {0:04x}".format(deviceId)
                    print "    device version: {0:02x}".format(version)
                    print "    input cluster count: {0:02x}".format(inCount)
                    position = 12
                    # input cluster list (16 bit words)
                    incls, position = getItemList(position, 2, inCount, r)
                    outCount, = unpack("<B",r[position])
                    position += 1
                    print "    output cluster count: {0:02x}".format(outCount)
                    #output cluster list (16 bit words)
                    outcls, position = getItemList(position, 2, outCount, r)
                    print "Cluster List...Completed!"
                
                print "Found (",(incls + outcls).__len__(), ")", repr(incls + outcls)
                clusters = []
                for c in incls + outcls:
                    #print "Adding cluster: ", repr(c)
                    cls = {"profile_id": profileId, "cls_id":c}
                    clusters.append(cls)
                    #print "Added cls num: ", clusters.__len__()
                    node['clusters'] = clusters
            except:
                print "error parsing Simple Descriptor"
                self.binDump(rfdata)
        elif (zcls == 0x0006):
            # Match Descriptor Request
            print "-------------Match Descriptor Request (rf_data len: ", rfdata.__len__(), ") --------------"
            binDump(rfdata)
            pos=0
            tx_id, nwk_addr, profileId, in_cls_num = unpack('<BHHB',rfdata[pos:pos+6])
            pos += 6
            if (in_cls_num > 0):
                incls, pos = getItemList(pos, 2, in_cls_num, rfdata)
                print "Input Clusters to match: ", repr(incls)
            out_cls_num, = unpack('<B',rfdata[pos])
            #print "out_cls_num: ", ord(out_cls_num)
            print "out_cls_num: ", out_cls_num
            pos += 1
            if (out_cls_num > 0):
                outcls, pos = getItemList(pos, 2, out_cls_num, rfdata)
                print "Output Clusters to match: ", repr(outcls)
            print "+++++++++++++ Sending 'Match Descriptor Response' +++++++++++++++++"
            #===================================================================
            print "Data to send: ", ('\x00' + '\x00' + '\x00' + '\x01' + '\x01')
            #frame_type='\x88'
            response = {'cmd':'tx_explicit',
                        'dest_addr_long':addr64,
                        'dest_addr': addr16,
                        'src_endpoint': '\x00',
                        'dest_endpoint':'\x00',
                        'cluster': '\x80' + chr(zcls), # cluster I want to deal with
                        'profile':'\x00\x00', # home automation profile
                        'data': chr(tx_id) + '\x00' + '\x00' + '\x00' + '\x01' + '\xaa'
                        }
            node = None
            #===================================================================
            #binDump(data)
            #pass
        else:
            print ("Unimplemented Cluster ID", hex(zcls))
            raise Exception("Unmanaged Message")
        return node, response
    
    def processChildTable(self, table):
        print "processChildTable: ", binDump(table)
        status = table[1]
        if(status != '\x00'):
            print "WARNING: returned status is: ", repr(statuscodes[status])
            return None
        if(len(table) > 12):
            nodes_num = ord(table[12])
            nodes = []
            idx = 14
            while (nodes_num > 0):
                nwk_addr = swpByteOrder(table[idx:idx+2])
                new_node = {'ieee_addr': 'none', 'nwk_addr': nwk_addr}
                idx+=2
                nodes_num-=1
                nodes.append(new_node)
        return nodes
        
    def processNeighborTable(self, node, table):
        binDump(table)
        status = table[1]
        if(status != '\x00'):
            print "WARNING: returned status is: ", repr(statuscodes[status])
            return None
        nodes_num = ord(table[4])
        nodes = []
        idx = 5 #offset 5+8 (1 seq + 4 table desc)
        while (nodes_num > 0):
            idx+=8 #8 ext panid
            ieee_addr = swpByteOrder(table[idx:idx+8])
            idx+=8
            nwk_addr = swpByteOrder(table[idx:idx+2])
            idx+=2
            new_node = {'ieee_addr': ieee_addr, 'nwk_addr': nwk_addr}
            nodes_num-=1
            nodes.append(new_node)
            #compensate offset for next node
            idx+=4 #node info (type, relation, radio, LQI, etc)
        return nodes
    
    
    
    
    