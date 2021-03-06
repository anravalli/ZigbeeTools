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
Created on 25 nov 2016

@author: andrea
'''

from struct import unpack
from pprint import _id
__frm_count = 0

clusters={'\x00\x00': 'Basic',
          '\x00\x01': 'Power Configuration',
          '\x00\x02': 'Device Temperature Configuration',
          '\x00\x03': 'Identify',
          '\x00\x04': 'Groups',
          '\x00\x05': 'Scenes',
          '\x00\x06': 'On/Off',
          '\x00\x07': 'On/Off Switch Configuration',
          '\x00\x08': 'Level Control',
          '\x00\x09': 'Alarms',
          '\x00\x0A': 'Time',
          '\x00\x0F': 'Binary Input (Basic)',
          '\x00\x19': 'OTA Update',
          '\x05\x00': 'IAS Zone',
          '\x05\x01': 'IAS ACE',
          '\x05\x02': 'IAS WD',
        }

statuscodes={'\x00': 'Success',
             '\xa3': 'ILLEGAL_REQUEST',
             '\xa6': 'INVALID_PARAMETER',
             '\xaa': 'NOT_SUPPORTED',
             '\xb0': 'UNSUPPORTED_ATTRIBUTE',
             '\x81': 'DEVICE_NOT_FOUND',
             '\x8c': 'UNREPORTABLE_ATTRIBUTE',
             }

datatypes={'\x00': {'name' :'no data', 'len': 0},
        '\x10':{'name' :'boolean', 'len': 1},
        '\x18':{'name' :'8 bit bitmap', 'len': 1},
        '\x19':{'name' :'16-bit bitmap', 'len': 2},
        '\x20':{'name' :'unsigned 8 bit integer', 'len': 1},
        '\x21':{'name' :'unsigned 16 bit integer', 'len': 4},
        '\x22':{'name' :'unsigned 24 bit integer', 'len': 4},
        '\x30':{'name' :'8 bit enumeration', 'len': 1},
        '\x31':{'name' :'16-bit enumeration', 'len': 2},
        '\x42':{'name' :'character string', 'len': 1},
        '\xf0':{'name' :'IEEE address', 'len': 8}
        }
zonetype={
    0x0000: 'standard CIE',
    0x0028: 'fire sensor',
    0x002a: 'water sensor',
    0x002b: 'gas sensor' 
    }
def setClusterSpecific(frm):
    return frm | 0b00000001

def swpByteOrder(arr):
    ret_list = []
    ret_str = ""
    i=len(arr)-1
    if (type(arr) is str):
        ret=ret_str
        while (i>=0):
            ret = ret + arr[i]
            i-=1
    elif (type(arr) is list):
        ret=ret_list
        while (i>=0):
            ret.append(arr[i])
            i-=1
    return ret

def printableOctet(b):
    if (type(b) is str):
        return str(bin(ord(b))[2:]).zfill(8)
    elif (type(b) is int):
        bb = chr(b)
        return str(bin(ord(bb))[2:]).zfill(8)
    else:
        raise TypeError("type must be a <str> or an <int>")

def printableByte(b):
    if (type(b) is str):
        return "{0:02x}".format(ord(b))
    elif (type(b) is int):
        return "{0:02x}".format(ord(chr(b)))
    else:
        raise TypeError("type must be a <str> or an <int>") 
    
def binDump(r_data):
    r_str = ""
    for b in r_data:
        #r_str.append("{0:02x}".format(ord(b))) #,
        r_str = r_str + ("{0:02x}".format(ord(b))) + " "
    #print " *"
    return r_str
    
def getItemList(spos, item_len, item_num, raw_data):
    items = []
    for x in range (0,item_num):
        thisOne, = unpack("<H",raw_data[spos : spos+item_len])
        items.append(raw_data[spos+1] + raw_data[spos])
        spos += item_len
        print "        item {0:04x}".format(thisOne)
    return items, spos

def getNextTxId():
    global __frm_count
    if (__frm_count < 256):
        _id = chr(__frm_count)
        return _id
    else:
        __frm_count = 0
        return chr(0)
        