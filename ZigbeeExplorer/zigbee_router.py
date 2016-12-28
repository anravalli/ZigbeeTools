#! /usr/bin/python

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

from XbeeCoordinator import XbeeCoordinator
from utils.Utils import getNextTxId, binDump, swpByteOrder, setClusterSpecific
#from xbee import ZigBee
#from xbee.helpers import dispatch

import logging
import time
import serial
import sys, traceback
from time import sleep
import threading

__running = False
	
def printDb(short=True):
	print "Print All Data in DB"
	#db_len = xbee.node_db.__len__()
	print "-- DB contains ", len, " nodes" 
	global lock
	lock.acquire()
	for node in xbee.node_db:
		print "node idx: ",node['entry']
		atrr = xbee._getAsString(node['node']['ieee_addr'])
		print "    ieee_addr: ",atrr
		atrr = xbee._getAsString(node['node']['nwk_addr'])
		print "    nwk_addr: ",atrr
		if (short==False):
			print "All node details goes here"
	lock.release()

def initNetwork():
	print "Init the NetworkDb"
	print("Wait while I locate the device")
	time.sleep(1)
	# First send a route record request so when the switch responds
	# I can get the addresses out of it
	BROADCAST = '\x00\x00\x00\x00\x00\x00\xff\xff'
	UNKNOWN = '\xff\xfe' # This is the 'I don't know' 16 bit address
	
	print "Broadcasting route record request (cluster = \x00\x32)"
	xbee.send('tx_explicit',
		dest_addr_long = BROADCAST,
		dest_addr = UNKNOWN,
		src_endpoint = '\x00',
		dest_endpoint = '\x00',
		cluster = '\x00\x32',
		profile = '\x00\x00',
		data = getNextTxId() + '\x01'
	)
	icount=0
	while (icount < 5):
		if (len(xbee.node_db) > 1):
			addr16 = xbee.node_db[1]['node']['nwk_addr']
			addr64 = xbee.node_db[1]['node']['ieee_addr']
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
			break
		print "Coordinator didn't respond yet...waiting"
		icount +=1
		sleep(1)
		
	
def getAttributes(addr64, addr16, cls):
	''' OK, now that I've listed the clusters, I'm going to see about 
	getting the attributes for one of them by sending a Discover
	attributes command.  This is not a ZDO command, it's a ZCL command.
	ZDO = ZigBee device object - the actual device
	ZCL = Zigbee cluster - the collection of routines to control it.
	frame control bits = 0b00 (this means a BINARY 00)
	manufacturer specific bit = 0, for normal, or one for manufacturer
	So, the frame control will be 0000000
	discover attributes command identifier = 0x0c
	then a zero to indicate the first attribute to be returned
	and a 0x0f to indicate the maximum number of attributes to 
	return.
    '''
	print "Sending Discover Attributes, Cluster:", repr(cls)
	xbee.send('tx_explicit',
	    dest_addr_long = addr64,
	    dest_addr = addr16,
	    src_endpoint = '\x00',
	    dest_endpoint = '\x01',
	    cluster = cls, # cluster I want to know about
	    profile = '\x01\x04', # home automation profile
	    # means: frame control 0, sequence number, command 0c, start at 0x00 for a length of 0x0f
	    data = '\x00' + getNextTxId() + '\x0c'+ '\x00' + '\x00'+ '\x0f'
	    )
	
def Identify():
	print 'Identify node'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	txid = getNextTxId()
	frm_type=setClusterSpecific(0b00000000)
	cls='\x00\x03'
	cmd='\x00' #read identify
	idfy_time = '\x05\x00' #5 secs
	dst_ep = '\x01'
	xbee.send('tx_explicit',
		dest_addr_long = addr64,
		dest_addr = addr16,
		src_endpoint = '\xaa',
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

def readBasicInfo():
	print 'Read Zone status'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	frm_type=0b00000000
	cmd='\x00' #read attr
	attributes=['\x00\x00','\x04\x00','\x05\x00','\x06\x00','\x07\x00']
	for attr in attributes:
		txid = getNextTxId()
		xbee.send('tx_explicit',
			dest_addr_long = addr64,
			dest_addr = addr16,
			src_endpoint = '\xaa',
			dest_endpoint = '\x01',
			cluster = '\x00\x00', # cluster I want to deal with
			profile = '\x01\x04', # home automation profile
			data = chr(frm_type) + txid + cmd + attr
		)
		sleep(1)

def readZoneStatus():
	print 'Read Zone status'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
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

def readZoneState():
	print 'Read Zone state'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
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

def readZoneId():
	print 'Read Zone ID'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
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

def readCieAddress():
	print 'Read CIE address'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	txid = getNextTxId()
	frm_type=0b00000000
	cmd='\x00' #read attr
	attr='\x10\x00' #attributes is CIE address 0010
	
	xbee.send('tx_explicit',
		dest_addr_long = addr64,
		dest_addr = addr16,
		src_endpoint = '\xaa',
		dest_endpoint = '\x01',
		cluster = '\x05\x00', # cluster I want to deal with
		profile = '\x01\x04', # home automation profile
		data = chr(frm_type) + txid + cmd + attr
	)

def writeCieAddress():
	print 'Write CIE address'
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	txid = getNextTxId()
	frm_type = 0b00010001 # 000: reserved, 1: no def res, 0: client->server, 0: no private ext, 01: cls specific
	cmd = '\x02' #write attr
	attr = '\x10\x00' #attributes is CIE address 0010
	data_type = '\xf0'
	#cie_add = swpByteOrder(xbee.node_db[1]['node']['ieee_addr'])
	cie_add = swpByteOrder(xbee.node_db[0]['node']['ieee_addr'])
	xbee.send('tx_explicit',
		dest_addr_long = addr64,
		dest_addr = addr16,
		src_endpoint = '\xaa',
		dest_endpoint = '\x01',
		cluster = '\x05\x00', # cluster I want to deal with
		profile = '\x01\x04', # home automation profile
		data = chr(frm_type) + txid + cmd + attr + data_type + cie_add
	)

def readChildTable():
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
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
	
def requestNeighborTable():
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
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
	
def selectNode():
	printDb()
	print "Please provide node index to select the node"
	str1 = raw_input(">")
	return str1
	
def getNodeDetails():
	node_idx = int(selectNode())
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	print 'Getting details from node: ', addr16
	xbee.send('tx_explicit',
		dest_addr_long = addr64,
		dest_addr = addr16,
		src_endpoint = '\x00',
		dest_endpoint = '\x00',
		cluster = '\x00\x05', # active endpoint request
		profile = '\x00\x00', # ZDO
		data = addr16[1]+addr16[0]
	)
	sleep(1)
	xbee.send('tx_explicit',
        dest_addr_long = addr64,
        dest_addr = addr16,
        src_endpoint = '\x00',
        dest_endpoint = '\x00', # ZDO ep - This has to go to endpoint 0 !
        cluster = '\x00\x04', #simple descriptor request'
        profile = '\x00\x00', # ZDO
        data = getNextTxId() + addr16[1] + addr16[0] + '\x01'
    )
	sleep(4)
	print "Num of clusters: ", xbee.node_db[node_idx]['node']['clusters'].__len__()
	for c in xbee.node_db[node_idx]['node']['clusters']:
		print "Getting attribute: ", c
		getAttributes(addr64, addr16, c['cls_id']) # Now, go get the attribute list for the cluster

def ui():
	str1 = raw_input(">")
	# Turn Switch Off
	if(str1[0] == '0'): 
		readChildTable()
	elif (str1[0] == '1'):
		requestNeighborTable()
	elif (str1[0] == '2'):
		readBasicInfo()
	elif (str1[0] == '3'):
		getNodeDetails()
	elif (str1[0] == '4'):
		Identify()
	elif (str1[0] == '5'): 
		readCieAddress()
	elif (str1[0] == '6'):
		writeCieAddress()
	elif (str1[0] == '7'): 
		readZoneState()
	elif (str1[0] == '8'): 
		readZoneStatus()
	elif (str1[0] == '9'):
		readZoneId()
	elif (str1[0] == 'p' or str1[0] == 'P'):
		printDb(short=False)
	elif (str1[0] == "q" or str1[0] == "Q"):
		global __running
		#print "Is runnung? ", __running
		__running = False
		
def printMenu():
	print "Select one of the following actions:"
	print "  0. Read Child Table"
	print "  1. Request Neighbor Table"
	print "  2. Query Basic Info"
	print "  3. Getting details from node"
	print "  4. Identify"
	print "  5. Read CIE address"
	print "  6. Write CIE address"
	print "  7. Read Zone state"
	print "  8. Read Zone status"
	print "  9. Read Zone ID"
	print "Additionally you can select:"
	print "  (P) Print out the whole node DB"
	print "  (Q) Quit this application"
	
if __name__ == "__main__":
	print "Start Application"

	ZIGBEEPORT = "/dev/ttyS2"
	if (len(sys.argv) > 1):
		ZIGBEEPORT = sys.argv[1]
	
	#ZIGBEEPORT = "COM3"
	ZIGBEEBAUD_RATE = 9600

	try:
		lock = threading.Lock()
		ser = serial.Serial(ZIGBEEPORT, ZIGBEEBAUD_RATE)
		xbee = XbeeCoordinator(ser, lock)
	except:
		print "Unable to start (check the serial port definition)"
		print "Current zigbee port is: ", ZIGBEEPORT
		print "Exiting..."
		exit(0)

	logging.basicConfig()

	print "started at ", time.strftime("%A, %B, %d at %H:%M:%S")
	__running = True
	initNetwork()
	printMenu()
	while __running:
		try:
			ui()
		except IndexError:
			printMenu()
		except KeyboardInterrupt:
			print "Keyboard interrupt"
			break
		except NameError as e:
			print "NameError:",
			print e.message.split("'")[1]
			traceback.print_exc(file=sys.stdout)
		except:
			print "Unexpected error:", sys.exc_info()[0]
			traceback.print_exc(file=sys.stdout)
			break
	sys.stdout.flush() # if you're running non interactive, do this
	print ("After the while loop")
	# halt() must be called before closing the serial
	# port in order to ensure proper thread shutdown
	xbee.halt()
	ser.close()