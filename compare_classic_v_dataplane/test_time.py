
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
class P4dht(Packet):
    name = "P4dht"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"SEND_TO_CONTROLLER", 2:"LOOKUP_IN", 3:"LOOKUP_OUT" }),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="gid", default=1, size=6),
                        BitField(name="counter", default=0, size=10)]

bind_layers(IP, P4dht, proto=2)
bind_layers(Ether, IP, type=0x800)

q=1
job=0
packets=17
table_classic=0
table_one_hop=0
recieved_ip_classic=list()
recieved_ip_onehop=list()
recieved_dht=list()


def send_dht(ip, ID, message="DHT message for testing" ,direction=2):
    global ring_size
    #ID=bin(ID)
    #ID=ID.zfill(ring_size)
    #print "Sending packet with id: "+str(ID)
    ip=ip.split("/")[0]
    addr = socket.gethostbyname(ip)
    pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / P4dht(message_type=direction, ID=int(ID), gid=1 , counter=0) / message)
    print (pkt, "hi")

    sendp(pkt, iface="eth0")
    return

def send_baseline(ip, message):
    send_ip(ip, "one_hop:"+message)
    send_ip(ip, "classic"+message)
    return

def send_ip(ip, message, ttl=50):
    ip=ip.split("/")[0]
    #ip="10.0.1.1"
    addr = socket.gethostbyname(ip)

    print "sending "+ message
    pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) /IP(dst=addr, ttl=ttl)/ message)
    print "ttl before seinding "+ str(pkt[IP].ttl)


    #print (pkt)
    sendp(pkt, iface="eth0")
    return

def print_pack(pkt):
    global recieved_dht
    global recieved_ip_classic
    global recieved_ip_onehop
    global table_classic
    global table_one_hop
    global job


    now=time.time()
    sys.stdout.flush()
    #print pkt
    if IP in pkt:
        hops=str(50-int(pkt[IP].ttl))
        if pkt[IP].proto==2:


            print pkt[P4dht].ID,
            #print "switches passed: ", pkt[P4dht].counter
            if (not pkt[P4dht].counter==0):
                tim= (str(pkt[P4dht].payload)).split(" ")[1]
                now=-1*(float(tim)-now)
                recieved_dht.append((str(now)+","+str(hops)))
                print now
        else:

            ttl=str(pkt[IP].ttl)
            if ICMP in pkt:
                return
            if (not ttl=="50"):
                str(pkt[IP].ttl)


                mes=str(pkt[IP].payload)
                print mes, str(job)
                if ("dh" in str(pkt[IP].payload) and not str(job) in mes):


                    id=str(mes).split(",")[1]
                    print str(mes)

                    mes=re.search(("dh.*"), str(mes))
                    if mes:
                        mes=mes.group(0)
                    else:
                        raise ValueError("dht not found")
                    id=int(id)

                    print id, "id"
                    if "one_hop" in str(pkt[IP].payload):
                        res=table_one_hop.evaluate(id=id)


                    elif "classic" in str(pkt[IP].payload):
                        res=table_classic.evaluate(id=id)

                    else:
                        raise ValueError ("Neither proto version found in message "+ str(pkt[IP].payload))

                    if res==0:

                        print "h"
                        now= -1*(float(mes.split(",")[2])-now)
                        if "one_hop" in str(pkt[IP].payload):
                            hops=str(50-int(pkt[IP].ttl))
                            recieved_ip_onehop.append(str(now)+"*"+hops+"*"+str(id))
                            print "one hop at final location with ID: "+  str(id) +" with "+str(hops)+" hops"
                        else:
                            hops=str(50-int(pkt[IP].ttl))
                            recieved_ip_classic.append(str(now)+"*"+hops+"*"+str(id))
                            print "classic at final location with ID: "+ str(id) +" with "+str(hops)+" hops"

                        return
                    else:
                        print res
                        mes=str(pkt[IP].payload)+","+ str(job)
                        send_ip(ip=res,message=mes, ttl=pkt[IP].ttl)




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
            while ("_c" in hosts.keys()[ip]):
                ip=random.randrange(0,len(hosts.keys()))
            ip=str(hosts[hosts.keys()[ip]]["ip"])
            print ip
            message=str(time.time())
            send_dht(ip, id, message="INnet: "+message)
            message=time.time()
            #print message
            send_baseline(ip=ip, message=("dht,"+str(id)+","+str(message)))
            time.sleep(.7)
    print "finished, sent "+str(64*packets)+" packets per protocol."

def main():
    global job
    global table_classic
    global table_one_hop
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
        table_one_hop=classic_dht.table_one_hop(name=job)
        table_classic= classic_dht.table(name=job)
        recieve()
        #print recieved_dht, recieved_ip
        if (not job=="client"):
            print "recieved Dht= "+ str(len(recieved_dht)) + ", recieved ip with one hop= "+str (len(recieved_ip_onehop))+ ", recieved ip with classic= "+ str(len(recieved_ip_classic))
            result=dict({"ip_onehop":recieved_ip_onehop,"ip_classic": recieved_ip_classic, "dht":recieved_dht})
            with open ("./test_logs/"+str(job)+".json", "w+") as f:
                json.dump(result, f, sort_keys=True, indent=4)





if __name__ == '__main__':

    main()
