'''
Created on 13 nov 2016

@author: RavalliAn
'''
from struct import unpack

class ZDO_Handler(object):
    '''
    classdocs
    '''
    def __init__(self, params):
        '''
        Constructor
        '''
    def hadle(self, zcls, addr64, addr16, rfdata):
        switchLongAddr = 0
        switchShortAddr = 0
        if (zcls == 0x0000):
            print ("Network (16-bit) Address Request")
            #printData(data)
        elif (zcls == 0x0008):
            # I couldn't find a definition for this 
            print("This was probably sent to the wrong profile")
        elif (zcls == 0x0004):
            # Simple Descriptor Request, 
            print("Simple Descriptor Request")
            print("I don't respond to this")
            #printData(data)
        elif (zcls == 0x0013):
            # This is the device announce message.
            print 'Device Announce Message'
            #printData(data)
            # This is a newly found device, so I'm going to tell it to 
            # report changes to the switch.  There are better ways of
            # doing this, but this is a test and demonstration
            print "sending 'configure reporting'"
            self.send('tx_explicit',
                dest_addr_long = switchLongAddr,
                dest_addr = switchShortAddr,
                src_endpoint = '\x00',
                dest_endpoint = '\x01',
                cluster = '\x00\x01', # cluster I want to deal with
                profile = '\x01\x04', # home automation profile
                data = '\x00' + '\xaa' + '\x06' + '\x00' + '\x00' + '\x00' + '\x10' + '\x00' + '\x00' + '\x00' + '\x40' + '\x00' + '\x00'
            )
        elif (zcls == 0x8000):
            print("Network (16-bit) Address Response")
            #printData(data)
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
            self.send('tx_explicit',
                dest_addr_long = addr64,
                dest_addr = addr16,
                src_endpoint = '\x00',
                dest_endpoint = '\x00', # This has to go to endpoint 0 !
                cluster = '\x00\x04', #simple descriptor request'
                profile = '\x00\x00',
                data = '\x13' + addr16[1] + addr16[0] + '\x01'
            )
        elif (zcls == 0x8004):
            print "simple descriptor response"
            try:
                clustersFound = []
                r = rfdata
                if (ord(r[1]) == 0): # means success
                    #take apart the simple descriptor returned
                    endpoint, profileId, deviceId, version, inCount = \
                        unpack('<BHHBB',r[5:12])
                    print "    endpoint reported is: {0:02x}".format(endpoint)
                    print "    profile id:  {0:04x}".format(profileId)
                    print "    device id: {0:04x}".format(deviceId)
                    print "    device version: {0:02x}".format(version)
                    print "    input cluster count: {0:02x}".format(inCount)
                    position = 12
                    # input cluster list (16 bit words)
                    for x in range (0,inCount):
                        thisOne, = unpack("<H",r[position : position+2])
                        clustersFound.append(r[position+1] + r[position])
                        position += 2
                        print "        input cluster {0:04x}".format(thisOne)
                    outCount, = unpack("<B",r[position])
                    position += 1
                    print "    output cluster count: {0:02x}".format(outCount)
                    #output cluster list (16 bit words)
                    for x in range (0,outCount):
                        thisOne, = unpack("<H",r[position : position+2])
                        clustersFound.append(r[position+1] + r[position])
                        position += 2
                        print "        output cluster {0:04x}".format(thisOne)
                    clustersFound.append('\x0b\x04')
                    print "added special cluster"
                    print "Completed Cluster List"
            except:
                print "error parsing Simple Descriptor"
                self.printData(rfdata)
            print repr(clustersFound)
            for c in clustersFound:
                self.getAttributes(addr64, addr16, c) # Now, go get the attribute list for the cluster
        elif (zcls == 0x0006):
        #print "Match Descriptor Request"
        # Match Descriptor Request
        #printData(data)
            pass
        else:
            print ("Unimplemented Cluster ID", hex(zcls))
            print

    def getAttributes(self, addr64, addr16, cls):
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
        self.send('tx_explicit',
            dest_addr_long = addr64,
            dest_addr = addr16,
            src_endpoint = '\x00',
            dest_endpoint = '\x01',
            cluster = cls, # cluster I want to know about
            profile = '\x01\x04', # home automation profile
            # means: frame control 0, sequence number 0xaa, command 0c,
            # start at 0x0000 for a length of 0x0f
            data = '\x00' + '\xaa' + '\x0c'+ '\x00' + '\x00'+ '\x0f'
            )