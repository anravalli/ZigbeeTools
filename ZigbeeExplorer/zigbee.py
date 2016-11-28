#! /usr/bin/python

'''
This is an examination of a REAL ZigBee device.  The CentraLite 4256050-ZHAC
		It has an impressive array of capabilities that I don't delve into in depth in
this examination, but it responds properly to the various ZigBee commands and holds
the clusters necessary to control a switch.
		Nice little device
'''


from XbeeCoordinator import XbeeCoordinator
from Utils import getNextTxId
#from xbee import ZigBee
#from xbee.helpers import dispatch

import logging
import time
import serial
import sys, traceback
from time import sleep
import threading
from Utils import swpByteOrder
'''
Before we get started there's a piece of this that drove me nuts.  Each message to a 
Zigbee cluster has a transaction sequence number and a header.  The transaction sequence
number isn't talked about at all in the Zigbee documentation (that I could find) and 
the header byte is drawn  backwards to everything I've ever dealt with.  So, I redrew 
the header byte so I could understand and use it:

7 6 5 4 3 2 1 0
      X          Disable Default Response 1 = don't return default message
        X        Direction 1 = server to client, 0 = client to server
          X      Manufacturer Specific 
              X  Frame Type 1 = cluster specific, 0 = entire profile
         
So, to send a cluster command, set bit zero.  If you want to be sure you get a reply, clear the default response.  I haven't needed the manufacturer specific bit yet.
'''
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
	
def printMenu():
	print "Select one of the following actions:"
	print "  1. Read Zone state"
	print "  2. Read Zone status"
	print "  3. Read CIE address"
	print "  4. Write CIE address"
	print "  5. Getting details from node"
	print "Additionally you can select:"
	print "  (P) Print out the whole node DB"
	print "  (Q) Quit this application"

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
		src_endpoint = '\x00',
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
		src_endpoint = '\x00',
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
		src_endpoint = '\x00',
		dest_endpoint = '\x01',
		cluster = '\x05\x00', # cluster I want to deal with
		profile = '\x01\x04', # home automation profile
		data = chr(frm_type) + txid + cmd + attr
	)

def writeCieAddress():
	print 'Write CIE address'
	node_idx = int(selectNode())
	switchShortAddr = xbee.node_db[node_idx]['node']['nwk_addr']
	switchLongAddr = xbee.node_db[node_idx]['node']['ieee_addr']
	txid = getNextTxId()
	frm_type = 0b00000000
	cmd = '\x02' #write attr
	attr = '\x10\x00' #attributes is CIE address 0010
	data_type = '\xf0'
	#cie_add = swpByteOrder(xbee.node_db[1]['node']['ieee_addr'])
	cie_add = swpByteOrder(xbee.node_db[0]['node']['ieee_addr'])
	xbee.send('tx_explicit',
		dest_addr_long = switchLongAddr,
		dest_addr = switchShortAddr,
		src_endpoint = '\x00',
		dest_endpoint = '\x01',
		cluster = '\x05\x00', # cluster I want to deal with
		profile = '\x01\x04', # home automation profile
		data = chr(frm_type) + txid + cmd + attr + data_type + cie_add
	)
	
def selectNode():
	printDb()
	print "Please provide node index to select the node"
	str1 = raw_input(">")
	return str1
	
def getNodeDetails():
	node_idx = int(selectNode())
	switchShortAddr = xbee.node_db[node_idx]['node']['nwk_addr']
	switchLongAddr = xbee.node_db[node_idx]['node']['ieee_addr']
	print 'Getting details from node: ', switchShortAddr
	xbee.send('tx_explicit',
		dest_addr_long = switchLongAddr,
		dest_addr = switchShortAddr,
		src_endpoint = '\x00',
		dest_endpoint = '\x00',
		cluster = '\x00\x05', # active endpoint request
		profile = '\x00\x00', # ZDO
		data = switchShortAddr[1]+switchShortAddr[0]
	)
	sleep(1)
	xbee.send('tx_explicit',
        dest_addr_long = switchLongAddr,
        dest_addr = switchShortAddr,
        src_endpoint = '\x00',
        dest_endpoint = '\x00', # ZDO ep - This has to go to endpoint 0 !
        cluster = '\x00\x04', #simple descriptor request'
        profile = '\x00\x00', # ZDO
        data = getNextTxId() + switchShortAddr[1] + switchShortAddr[0] + '\x01'
    )
	sleep(4)
	print "Num of clusters: ", xbee.node_db[node_idx]['node']['clusters'].__len__()
	for c in xbee.node_db[node_idx]['node']['clusters']:
		print "Getting attribute: ", c
		getAttributes(switchLongAddr, switchShortAddr, c['cls_id']) # Now, go get the attribute list for the cluster

def ui():
	str1 = raw_input(">")
	# Turn Switch Off
	if(str1[0] == '0'): 
		print 'Not implemented'
	elif (str1[0] == '1'): 
		readZoneState()
	elif (str1[0] == '2'): 
		readZoneStatus()
	elif (str1[0] == '3'): 
		readCieAddress()
	elif (str1[0] == '4'):
		writeCieAddress()
	elif (str1[0] == '5'):
		getNodeDetails()
	elif (str1[0] == 'p' or str1[0] == 'P'):
		printDb(short=False)
	elif (str1[0] == "q" or str1[0] == "Q"):
		global __running
		#print "Is runnung? ", __running
		__running = False
	
if __name__ == "__main__":
	print "Start Application"

	#ZIGBEEPORT = "/dev/ttyUSB1"
	ZIGBEEPORT = "COM3"
	ZIGBEEBAUD_RATE = 9600

	try:
		lock = threading.Lock()
		ser = serial.Serial(ZIGBEEPORT, ZIGBEEBAUD_RATE)
		xbee = XbeeCoordinator(ser, lock)
	except:
		print "Unable to start (check the serial port definition)"
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