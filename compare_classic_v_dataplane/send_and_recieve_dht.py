#!/usr/bin/env python

import argparse
import sys
import socket
import random
import struct
import re
import logging
import threading
import time


from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump

from scapy.all import bind_layers
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
import readline

ring_size=6

class P4dht(Packet):
    name = "P4dht"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"SEND_TO_CONTROLLER", 2:"LOOKUP_IN", 3:"LOOKUP_OUT" }),
                        BitField(name="gid", default=1, size=6),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="counter", default=0, size=10)]

bind_layers(Ether, P4dht, type=0x1212)
bind_layers(Ether, IP, type=0x800)
q=1
direction=2

def user_input(my_id, direction):
    """
    Functions supported:


    send-
    send a packet, options Packet id=number within id space
    message= (per default) "DHT message from (this id) :D"
    default will assign id for packet

    quit
    end program
    """
    global q

    while (q):

        input = raw_input("Enter command to either send message or quit: S/q  ")

        sys.stdout.flush()


        match=re.search("^[\s]*[sS]+", input)
        qmatch= re.search(r"(?i)^q", input)

        if (match):


            match=re.search(r"(?i)-id=[\d]+", input)
            if (match):
                tmp=re.split("=", match.group(0))
                id=int(tmp[-1])
            else:
                id=random.randrange(0,64)
            match=re.search(r"(?i)-m=.+", input)
            if (match):
                tmp=re.split("=", match.group(0))
                message=str(tmp[-1])
            message="DHT message with ID "+str(id)+my_id
            send(ID=id,message=message,direction=direction)

        elif qmatch:

            return -1
        else:
            print ("Invalid command, either s [-id=....] [-m=....] or q for quit (in brackets is optional)")


def send(ID, message="test rewrite",direction=0, gid=1):
    global ring_size
    #ID=bin(ID)
    #ID=ID.zfill(ring_size)
    print "Sending packet with id: "+str(ID)
    print ID, message

    pkt = (Ether(dst='00:04:00:00:00:00', type=0x1212) / P4dht(message_type=direction, ID=int(ID), counter=0) / (message))
    print (pkt)

    sendp(pkt, iface="eth0")


def print_pack(pkt):

    sys.stdout.flush()
    #print "hi"
    if P4dht in pkt:
        if (not pkt[P4dht].counter==0):
            print pkt
        else:
            print "sen  t"


def recieve():

    print "waiting to recieve packets...."
    print " "

    iface = 'eth0'
    #sniff(filter="P4dht", iface=iface)

    try:
        sys.stdout.flush()
        sniff(prn=print_pack)
    except KeyboardInterrupt:
        print "shutting down"
        return -1

def main():
    global direction
    if (len(sys.argv)>1):
        my_id="from " + str(sys.argv[1])
    else:
        my_id=" "
    if (len(sys.argv)>2):

        match= re.search(r"(?i)\s*in", sys.argv[2])
        if type(sys.argv[2]==int):
            if sys.argv[2]<=0:
                direction=2  #
        elif (match):
            direction=2

        match= re.search(r"(?i)\s*out", sys.argv[2] )
        if type(sys.argv[2]==int):
            if sys.argv[2]>0:
                direction=3  #
        elif (match):
            direction=3

    else:
        direction=2  #

    print "Starting server/client "+my_id


    r=threading.Thread(target=user_input, args=(my_id, direction))
    r.start()
    q=recieve()
    r.join()




if __name__ == '__main__':

    main()
