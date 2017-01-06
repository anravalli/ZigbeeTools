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
  along with ZigbeeTools; see the file COPYING.  If not, see
  <http://www.gnu.org/licenses/>.
  
'''

from XbeeCoordinator import XbeeCoordinator
from coord_commands import *
#from xbee import ZigBee
#from xbee.helpers import dispatch

import logging
import serial
import sys, traceback
from time import strftime
import threading
from utils import Utils

__running = False
	
def printDb(short=True):
	print "Print All Data in DB"
	#db_len = xbee.node_db.__len__()
	print "-- DB contains ", len(xbee.node_db), " nodes" 
	global lock
	lock.acquire()
	for node in xbee.node_db:
		#atrr = xbee._getAsString(node['node']['ieee_addr'])
		print str(node['entry']) + ". NWK_Addr: " + binDump(node['node']['nwk_addr'])
		#atrr = xbee._getAsString(node['node']['nwk_addr'])
		print "    ieee_addr: "+ binDump(node['node']['ieee_addr'])
		if (short==False):
			try:
				for c in node['node']['clusters']:
					cid = c['cls_id']
					print "cluster ( " + binDump(cid) + "): " + Utils.clusters[cid]
					print "    Attributes: {0}".format(c['attributes'])
			except KeyError:
				print "No cluster for this node"
			
	lock.release()

def initNetwork():
	print "Init the NetworkDb"
	print("Wait while I locate the device")
	sleep(1)
	
	BROADCAST = '\x00\x00\x00\x00\x00\x00\xff\xff'
	#UNKNOWN = '\xff\xfe' # This is the 'I don't know' 16 bit address
	execCommand(getIeeeAddress, 0, '\x00\x00',BROADCAST)
	icount=0
	while (icount < 5):
		if (len(xbee.node_db) > 0):
			execCommand(getNeighborTable, 0)
			print "...."
			break
		print "Coordinator didn't respond yet...waiting"
		icount +=1
		sleep(1)
		
def getNodeDetails():
	addr16 = xbee.node_db[0]['node']['nwk_addr']
	addr64 = xbee.node_db[0]['node']['ieee_addr']
	node_idx = int(selectNode())
	print 'Getting details from node: ', addr16
	#getActiveEndPoints
	execCommand(getActiveEndPoints, node_idx)
	sleep(1)
	#getSimpleDescriptor
	execCommand(getSimpleDescriptor, node_idx)
	sleep(4)
	print "Num of clusters: ", xbee.node_db[node_idx]['node']['clusters'].__len__()
	addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	for c in xbee.node_db[node_idx]['node']['clusters']:
		print "Getting attribute: ", c
		getAttributes(xbee, addr64, addr16, c['cls_id']) # Now, go get the attribute list for the cluster
		
def selectNode():
	printDb()
	print "Please provide node index to select the node"
	str1 = raw_input(">")
	return str1

def execCommand(cmd=None, node_idx=-1, addr16='', addr64=''):
	if cmd==None:
		print "ERROR - no command to execute provided"
		return -3
	if node_idx == -1:
		node_idx = int(selectNode())
	if addr16 == '':
		addr16 = xbee.node_db[node_idx]['node']['nwk_addr']
	if addr64 == '':
		addr64 = xbee.node_db[node_idx]['node']['ieee_addr']
	print "request exec to: " + binDump(addr16) + " " +  binDump(addr64)
	cmd(xbee, addr64, addr16)

def pollNeighborTable():
	while True:
		print "************ ", strftime("%A, %B, %d at %H:%M:%S"), "***************************"
		execCommand(getNeighborTable, 0)
		sleep(1800)

def ui():
	str1 = raw_input(">")
	# Turn Switch Off
	if(str1[0] == '0'): 
		execCommand(readChildTable)
	elif (str1=='10'):
		execCommand(readPowerConfig)
	elif (str1[0] == '1'):
		execCommand(requestNeighborTable)
	elif (str1[0] == '2'):
		execCommand(readBasicInfo)
	elif (str1[0] == '3'):
		getNodeDetails()
	elif (str1[0] == '4'):
		Identify()
	elif (str1[0] == '5'): 
		execCommand(readCieAddress)
	elif (str1[0] == '6'):
		execCommand(writeCieAddress)
	elif (str1[0] == '7'): 
		execCommand(readZoneState)
	elif (str1[0] == '8'): 
		print 'Read Zone status'
		execCommand(readZoneStatus)
	elif (str1[0] == '9'):
		execCommand(readZoneId)
	elif (str1[0] == 'm'):
		#monitorLoop()
		pollNeighborTable()
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
	#print "  (M) Enter in monitor loop"
	print "  (P) Print out the whole node DB"
	print "  (Q) Quit this application"

def print_help():
	print "This tool is meant to help check/implement a Zigbee coordinator"
	print "Usage:"
	print "Start the tool:\n\t./zigbee_coordinator.py <serial_port>"
	print "Print this help message:\n\t./zigbee_coordinator.py -h"
	exit(0)
	
if __name__ == "__main__":
	print "Start Application"

	ZIGBEEPORT = "/dev/ttyS2"
	if (len(sys.argv) > 1):
		if(sys.argv[1]=="-h"):
			print_help()
		else:
			ZIGBEEPORT = sys.argv[1]
	else:
		print "ERROR: not enough or too many parameters!"
		print_help()
	
	ZIGBEEBAUD_RATE = 9600

	try:
		lock = threading.Lock()
		ser = serial.Serial(ZIGBEEPORT, ZIGBEEBAUD_RATE)
		xbee = XbeeCoordinator(ser, lock)
	except:
		print "Unable to start (check the serial port definition)"
		print "Current zigbee port is: ", ZIGBEEPORT
		print "Exiting..."
		exit(1)

	logging.basicConfig()

	print "started at ", strftime("%A, %B, %d at %H:%M:%S")
	__running = True
	initNetwork()
	
	xbee.setMonitorFunction(readZoneStatus)
	
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
	
	