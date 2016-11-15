#! /usr/bin/python

'''
This is an examination of a REAL ZigBee device.  The CentraLite 4256050-ZHAC
		It has an impressive array of capabilities that I don't delve into in depth in
this examination, but it responds properly to the various ZigBee commands and holds
the clusters necessary to control a switch.
		Nice little device
'''


from XbeeCoordinator import XbeeCoordinator

#from xbee import ZigBee
#from xbee.helpers import dispatch

import logging
#import datetime
import time
import serial
import sys, traceback
#import shlex

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
switchLongAddr = '12'
switchShortAddr = '12'

def printDb():
	print "Print All Data in DB"

def initNetwork():
	print "Init the NetworkDb"
	print("Wait while I locate the device")
	time.sleep(1)
	# First send a route record request so when the switch responds
	# I can get the addresses out of it
	print "Broadcasting route record request (cluster = \x00\x32)"
	xbee.send('tx_explicit',
		dest_addr_long = BROADCAST,
		dest_addr = UNKNOWN,
		src_endpoint = '\x00',
		dest_endpoint = '\x00',
		cluster = '\x00\x32',
		profile = '\x00\x00',
		data = '\x12'+'\x01'
	)
		
if __name__ == "__main__":
	#------------ XBee Stuff -------------------------
	# this is the /dev/serial/by-id device for the USB card that holds the XBee
	ZIGBEEPORT = "COM6"
	ZIGBEEBAUD_RATE = 9600
	# Open serial port for use by the XBee
	ser = serial.Serial(ZIGBEEPORT, ZIGBEEBAUD_RATE)
	xbee = XbeeCoordinator(ser)

	# The XBee addresses I'm dealing with
	BROADCAST = '\x00\x00\x00\x00\x00\x00\xff\xff'
	UNKNOWN = '\xff\xfe' # This is the 'I don't know' 16 bit address

	#-------------------------------------------------
	logging.basicConfig()

	# Create XBee library API object, which spawns a new thread
	
	print "started at ", time.strftime("%A, %B, %d at %H:%M:%S")
	initNetwork()
	while True:
		try:
			str1 = raw_input("")
			# Turn Switch Off
			if(str1[0] == '0' or str1[0] == '1' or str1[0] == '2'):
				print 'Not implemented'
			# Turn Switch On
			if(str1[0] == '3'):
				printDb()
			elif (str1[0] == '4'):
				print 'Do something...'
# 				xbee.send('tx_explicit',
# 					dest_addr_long = switchLongAddr,
# 					dest_addr = switchShortAddr,
# 					src_endpoint = '\x00',
# 					dest_endpoint = '\x01',
# 					cluster = '\x00\x06', # cluster I want to deal with
# 					profile = '\x01\x04', # home automation profile
# 					data = '\x00'+'\xaa'+'\x00'+'\x00'+'\x00'
# 				)
			elif (str1[0] == '4'):
				print 'Get Report from Switch'
				xbee.send('tx_explicit',
					dest_addr_long = switchLongAddr,
					dest_addr = switchShortAddr,
					src_endpoint = '\x00',
					dest_endpoint = '\x00',
					cluster = '\x00\x05', # cluster I want to deal with
					profile = '\x00\x00', # home automation profile
					data = switchShortAddr[1]+switchShortAddr[0]
				)
		except IndexError:
			print "empty line, try again"
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