'''
Created on 13 nov 2016

@author: RavalliAn
'''

class HA_ProfileHandler(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def handle(self, zcls, addr64, addr16, rfdata):
        if (rfdata[0] == '\x08'): # was it successful?
            #should have a bit check to see if manufacturer data is here
            cCommand = rfdata[2]
            print "Cluster command: ", hex(ord(cCommand))
        else:
            cCommand = rfdata[2]
            print "Cluster command failed"
            return
        # grab the payload data to make it easier to work with
        payload = rfdata[3:] #from index 3 on is the payload for the command
        datatypes={'\x00':'no data',
            '\x10':'boolean',
            '\x18':'8 bit bitmap',
            '\x20':'unsigned 8 bit integer',
            '\x21':'unsigned 24 bit integer',
            '\x30':'8 bit enumeration',
            '\x42':'character string'}
        #print "Raw payload:",repr(payload)
        # handle these first commands in a general way
        if (cCommand == '\x0d'): # Discover Attributes
            # This tells you all the attributes for a particular cluster
            # and their datatypes
            print "Discover attributes response"
            if (payload[0] == '\x01'):
                print "All attributes returned"
            else:
                print "Didn't get all the attributes on one try"
            i = 1
            if (len(payload) == 1): # no actual attributes returned
                print "No attributes"
                return
            while (i < len(payload)-1):
                print "    Attribute = ", hex(ord(payload[i+1])) , hex(ord(payload[i])),
                try:
                    print datatypes[payload[i+2]]
                    i += 3
                except:
                    print "I don't have an entry for datatype:", hex(ord(payload[i+2]))
                    return

        if (zcls == 0x0000): # Under HA this is the 'Basic' Cluster
            pass
        elif (zcls == 0x0003): # 'identify' should make it flash a light or something 
            pass
        elif (zcls == 0x0004): # 'Groups'
            pass
        elif (zcls == 0x0005): # 'Scenes'  
            pass
        elif (zcls == 0x0006): # 'On/Off' this is for switching or checking on and off  
            #print "inside cluster 6"
            if cCommand in ['\x0a','\x01']:
                # The very last byte tells me if the light is on.
                if (payload[-1] == '\x00'):
                    print "Light is OFF"
                else:
                    print "Light is ON"
            pass
        elif (zcls == 0x0008): # 'Level'  
            pass
        else:
            print("Haven't implemented this yet")