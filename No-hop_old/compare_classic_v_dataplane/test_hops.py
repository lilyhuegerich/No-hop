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
import json


from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import bind_layers
import readline
import classic_dht
import send_and_recieve_dht as packets

ring_size=6
"""
class P4dht(Packet):
    name = "P4dht"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"SEND_TO_CONTROLLER", 2:"LOOKUP_IN", 3:"LOOKUP_OUT" }),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="counter", default=0, size=8)]"""

bind_layers(Ether, packets.P4dht, type=0x1212)
bind_layers(Ether, IP, type=0x800)

q=1
job=0
packets=16
table=0
recieved_ip=list()
recieved_dht=list()


def send_dht(ID, message="DHT message for testing" ,direction=2):
    global ring_size
    #ID=bin(ID)
    #ID=ID.zfill(ring_size)
    #print "Sending packet with id: "+str(ID)

    pkt = (Ether(dst='00:04:00:00:00:00', type=0x1212) / P4dht(message_type=direction, ID=int(ID), counter=0) / message)
    #print (pkt)
    sendp(pkt, iface="eth0")
    return

def send_ip(ip, message, ttl=50):
    ip=ip.split("/")[0]
    #ip="10.0.1.1"
    #addr = socket.gethostbyname(ip)
    addr=ip
    print type(addr), type(message), type(ttl)

    pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=ttl)/ message)
    print "ttl before seinding "+ str(pkt[IP].ttl)


    #print (pkt)
    sendp(pkt, iface="eth0")
    return

def print_pack(pkt):
    global recieved_dht
    global recieved_ip
    global table
    sys.stdout.flush()
    if P4dht in pkt:

        print pkt[P4dht].payload
        #print "switches passed: ", pkt[P4dht].counter
        if (not pkt[P4dht].counter==0):
            recieved_dht.append(pkt[P4dht].counter)
    if IP in pkt:

        ttl=str(pkt[IP].ttl)
        if ICMP in pkt:
            return
        if (not ttl=="50" and str(table.my_name) not in str(pkt[IP].payload)):
            str(pkt[IP].ttl)


            if ("dht" in str(pkt[IP].payload)):

                mes=pkt[IP].payload
                id=str(mes).split(",")[1]
                print str(mes)
                mes=re.search(("dht.*"), str(mes))
                if mes:
                    mes=mes.group(0)
                else:
                    raise ValueError("dht not found")

                id=int(id)
                print id, "id"
                res=table.evaluate(id=(id))

                if res==0:
                    print "h"
                    recieved_ip.append(str(mes)+str(table.my_name)+" ttl="+ttl)
                else:
                    mes=str(mes)+","+str(table.my_name)
                    send_ip(ip=res,message=mes, ttl=int(ttl))

                if (int(ttl)>50):
                    raise ValueError("shouldnt happen ttl is " +str(ttl) +" in message "+ mes)






def recieve():

    print "waiting to recieve packets...."
    print " "

    iface = 'eth0'
    #sniff(filter="P4dht", iface=iface)


    sys.stdout.flush()
    try:
        sniff(iface=iface, prn=print_pack)
    except KeyboardInterrupt:
        return

def send_packets(filename="topology.json"):
    with open(filename, "r") as f:
        topo=(json.load(f))

    hosts=topo["hosts"]
    #time.sleep(5) # to make sure all hosts are configured
    global ring_size
    global packets
    for i in range(64):
        for j in range (packets):
            print i
            id=i
            ip=random.randrange(0,len(hosts.keys()))
            ip=str(hosts[hosts.keys()[ip]]["ip"])
            print ip

            send_dht(id)
            send_ip(ip=ip, message=("dht,"+str(id)))
            time.sleep(.02)
    print "finished"

def main():
    global job
    global table
    global recieved_ip
    global recieved_dht
    if (len(sys.argv)>1):
        job =str(sys.argv[1])
    else:
        raise ValueError("Need to enter either job or host name")
    if (len(sys.argv)>2):
        filename=str(sys.argv[2])


    if job=="client":
        send_packets()
    else:

        table=classic_dht.table(name=job)
        recieve()
        print recieved_dht, recieved_ip
        if (not job=="client"):
            result=dict({"ip":recieved_ip, "dht":recieved_dht})
            with open ("./test_logs/"+str(table.my_name)+".json", "w+") as f:
                json.dump(result, f, sort_keys=True, indent=4)





if __name__ == '__main__':

    main()
