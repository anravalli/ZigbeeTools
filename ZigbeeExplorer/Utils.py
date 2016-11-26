'''
Created on 25 nov 2016

@author: andrea
'''

from struct import unpack
from pprint import _id
__frm_count = 0

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
    
def binDunp(r_data):
    for b in r_data:
        print "{0:02x}".format(ord(b)),
    print
    
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
        