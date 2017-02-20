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

from utils.Utils import getNextTxId, binDump, swpByteOrder, setClusterSpecific
from time import sleep

# ZDO commands

def do_Bind_req(xbee, addr64, addr16):
    print "Perform Bing_req"
    
    coord_ieee_addr = xbee.node_db[0]['node']['ieee_addr']
    
    txid = getNextTxId()
    SrcAddress = swpByteOrder(addr64)
    SrcEndp = '\x01'
    ClusterID = '\x01\x00' # 0001 power
    DstAddrMode = '\x03'
    DstAddress = swpByteOrder(coord_ieee_addr)
    DstEndp = '\x01'
    
    tx_data = txid + SrcAddress + SrcEndp + ClusterID + DstAddrMode + DstAddress + DstEndp
    xbee.send('tx_explicit',
        dest_addr_long = addr64, #,
        dest_addr = addr16, # 
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x21', # Bind_req 0x0021
        profile = '\x00\x00', # ZDO
        data = tx_data
    )
    
def getIeeeAddress(xbee, addr64, addr16):
    print "Getting Xbee IEEE address"
    txid = getNextTxId()
    tx_data = txid + '\x00\x00' + '\x01' + '\x00'
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x01', # IEEE address request
        profile = '\x00\x00', # ZDO
        data =tx_data
    )

def getNeighborTable(xbee, addr64, addr16):
    print 'Requesting Neighbor Table from node: ', binDump(addr16)
    txid = getNextTxId()
    start_idx = '\x00'
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x31', # Neighbor Table request
        profile = '\x00\x00', # ZDO
        data = txid + start_idx
    )

def getActiveEndPoints(xbee, addr64, addr16):
    print 'Getting Node Active End Points: ', binDump(addr16)
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x05', # active endpoint request
        profile = '\x00\x00', # ZDO
        data = getNextTxId() + addr16[1]+addr16[0]
    )

def getSimpleDescriptor(xbee, addr64, addr16):
    print 'Getting Node\'s Simple Descriptor: ', binDump(addr16)
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00', # ZDO ep - This has to go to endpoint 0 !
        cluster = '\x00\x04', #simple descriptor request'
        profile = '\x00\x00', # ZDO
        data = getNextTxId() + addr16[1] + addr16[0] + '\x01'
    )

def getAttributes(xbee, addr64, addr16, cls):
    print "Sending Discover Attributes, Cluster:", repr(cls)
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = cls, # cluster I want to know about
        profile = '\x01\x04', # home automation profile
        # means: frame control 0, sequence number, command 0c, start at 0x00 for a length of 0x0f
        data = '\x00' + getNextTxId() + '\x0c'+ '\x00' + '\x00'+ '\x0f'
        )

# HomeAutomation commands
def start_WdAlarm(xbee, addr64, addr16):
    print "Start Warning Device alarm"

    #ZCL header || Dir| Attr id | Attr. data type | Min int | Max Int | delta | Timeout
    frm_type=setClusterSpecific(0)
    txid = getNextTxId()
    cmd='\x00' #wd start alarm
    warn = 0b00101000 #
    warn_t = '\x00\xff'
    #squawk = 0b11010000 #
    tx_data = chr(frm_type)+ txid + cmd + chr(warn) + warn_t
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x05\x02', # WD Cluster
        profile = '\x01\x04', # HA
        data = tx_data
    )


def do_WdSqawk(xbee, addr64, addr16):
    print "Warning Device Squawk"

    #ZCL header || Dir| Attr id | Attr. data type | Min int | Max Int | delta | Timeout
    frm_type=setClusterSpecific(0)
    txid = getNextTxId()
    cmd='\x01' #wd squawk
    squawk = 0b00011011 #
    #squawk = 0b11010000 #
    tx_data = chr(frm_type)+ txid + cmd + chr(squawk)
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x05\x02', # WD Cluster
        profile = '\x01\x04', # HA
        data = tx_data
    )


def confg_AttrReport(xbee, addr64, addr16):
    print "Configure Attribute Report"

    #ZCL header || Dir| Attr id | Attr. data type | Min int | Max Int | delta | Timeout
    frm_type=0b00000000
    txid = getNextTxId()
    cmd='\x06' #configure reporting
    rep_dir = '\x00'
    attr_id = '\x21\x00'
    attr_type = '\x20'
    min_rep_t = '\x03\x00'
    max_rep_t = '\x3c\x00'
    delta = '\x01'
    tx_data = chr(frm_type)+ txid + cmd + rep_dir + attr_id + attr_type + min_rep_t + max_rep_t + delta
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x00\x01', # Power Configuration
        profile = '\x01\x04', # HA
        data = tx_data
    )

def Identify(xbee, addr64, addr16):
    print 'Identify node'
    txid = getNextTxId()
    frm_type=setClusterSpecific(0b00000000)
    cls='\x00\x03'
    cmd='\x00' #read identify
    idfy_time = '\x05\x00' #5 secs
    dst_ep = '\x01'
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = dst_ep,
        cluster = cls,
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + idfy_time
    )
    print '...sleep...'
    sleep(5)
    print 'Query identify time'
    cmd = '\x01'
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\xaa',
        dest_endpoint = dst_ep,
        cluster = cls,
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd
    )
    #attr='\x01\x00' #attributes is ZoneStatus 0002

def readBasicInfo(xbee, addr64, addr16):
    print 'Read Zone status'
    frm_type=0b00000000
    cmd='\x00' #read attr
    attributes=['\x00\x00','\x01\x00','\x02\x00','\x03\x00','\x04\x00','\x05\x00','\x06\x00',
                '\x07\x00','\x10\x00','\x11\x00','\x12\x00','\x13\x00',]
    for attr in attributes:
        print "Reading attribute: " + binDump(attr)
        txid = getNextTxId()
        xbee.send('tx_explicit',
            dest_addr_long = addr64,
            dest_addr = addr16,
            src_endpoint = '\x01',
            dest_endpoint = '\x01',
            cluster = '\x00\x00', # 
            profile = '\x01\x04', # home automation profile
            data = chr(frm_type) + txid + cmd + attr
        )
        sleep(1)

def writeLocation(xbee, addr64, addr16):
    print 'Write Location'
    frm_type=0b00000000 #profile wide
    cmd='\x02' #write attribute
    attr='\x10\x00'
    txid = getNextTxId()
    attr_type='\x42'
    attr_data_len='\x01'
    attr_data='\x31'#raw_input(">")
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x00\x00', # 
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr + attr_type + attr_data_len + attr_data
    )
    sleep(5)
    cmd='\x00' #read attribute
    txid = getNextTxId()
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x00\x00', # 
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr
    )

def readPowerConfig(xbee, addr64, addr16):
    print 'Read Power Config'
    frm_type=0b00000000
    cmd='\x00' #read attr
    B_SIZE= '\x31\x00' #0034
    B_NUM= '\x33\x00' #0034
    RATED_VOLT= '\x34\x00' #0034
    VOLT= '\x20\x00' #0020
    PERC_REMAIN= '\x21\x00' #0021
    attributes=[RATED_VOLT,VOLT,PERC_REMAIN,B_SIZE,B_NUM]
    for attr in attributes:
        txid = getNextTxId()
        xbee.send('tx_explicit',
            dest_addr_long = addr64,
            dest_addr = addr16,
            src_endpoint = '\xaa',
            dest_endpoint = '\x01',
            cluster = '\x00\x01', # cluster I want to deal with
            profile = '\x01\x04', # home automation profile
            data = chr(frm_type) + txid + cmd + attr
        )
        sleep(1)

def readZoneStatus(xbee, addr64, addr16):
    #print 'Read Zone status'
    txid = getNextTxId()
    frm_type=0b00000000
    cmd='\x00' #read attr
    attr='\x02\x00' #attributes is ZoneStatus 0002
    
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\xaa',
        dest_endpoint = '\x01',
        cluster = '\x05\x00', # cluster I want to deal with
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr
    )

def readZoneState(xbee, addr64, addr16):
    print 'Read Zone state'
    txid = getNextTxId()
    frm_type=0b00000000
    cmd='\x00' #read attr
    attr='\x00\x00' #attributes is ZoneState 0000
    
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\xaa',
        dest_endpoint = '\x01',
        cluster = '\x05\x00', # cluster I want to deal with
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr
    )

def readZoneId(xbee, addr64, addr16):
    print 'Read Zone ID'
    txid = getNextTxId()
    frm_type=0b00000000
    cmd='\x00' #read attr
    attr='\x11\x00' #attributes is ZoneID 11
    
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\xaa',
        dest_endpoint = '\x01',
        cluster = '\x05\x00', # cluster I want to deal with
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr
    )

def readCieAddress(xbee, addr64, addr16):
    print 'Read CIE address'
    txid = getNextTxId()
    frm_type=0b00000000
    cmd='\x00' #read attr
    attr='\x10\x00' #attributes is CIE address 0010
    
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x05\x00', # cluster I want to deal with
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr
    )

def writeCieAddress(xbee, addr64, addr16):
    print 'Write CIE address'
    txid = getNextTxId()
    #frm_type = 0b00010001 # 000: reserved, 1: no def res, 0: client->server, 0: no private ext, 01: cls specific
    frm_type = 0b00000000
    cmd = '\x02' #write attr
    attr = '\x10\x00' #attributes is CIE address 0010
    data_type = '\xf0'
    #cie_add = swpByteOrder(xbee.node_db[1]['node']['ieee_addr'])
    cie_add = swpByteOrder(xbee.node_db[0]['node']['ieee_addr'])
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x01',
        dest_endpoint = '\x01',
        cluster = '\x05\x00', # cluster I want to deal with
        profile = '\x01\x04', # home automation profile
        data = chr(frm_type) + txid + cmd + attr + data_type + cie_add
    )

def readChildTable(xbee, addr64, addr16):
    
    txid = getNextTxId()
    start_idx = '\x00'
    req_type = '\x01'
    print 'Requesting child table to node: ', binDump(addr16)
    #nk_addr64=swpByteOrder(addr64)
    tx_data = txid + swpByteOrder(addr16) + req_type + start_idx
    print "debug - data to send: ", binDump(tx_data)
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x01', # IEEE address request
        profile = '\x00\x00', # ZDO
        data =tx_data
    )
    
def requestNeighborTable(xbee, addr64, addr16):
    txid = getNextTxId()
    start_idx = '\x00'
    print 'Requesting Neighbor Table from node: ', addr16
    xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00',
        cluster = '\x00\x31', # Neighbor Table request
        profile = '\x00\x00', # ZDO
        data = txid + start_idx
    )
