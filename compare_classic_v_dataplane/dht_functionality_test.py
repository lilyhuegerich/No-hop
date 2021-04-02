import argparse
import sys
import socket
import random
import struct
import re
import logging
import threading
import time
import subprocess
import json
from time import sleep

from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField
from scapy.all import bind_layers
import readline

import send_and_recieve_dht
ring_size=6
counter=0
recieved=0
def print_pack(pkt):
    global counter
    sys.stdout.flush()
    if P4dht in pkt:
        if (not pkt[P4dht].counter==0):
            print pkt
            counter=counter+1
        else:
            print "sen  t"

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

def test():


    for i in range(2**6):
        print "sending test id= "+str(i)
        try:
            send_and_recieve_dht.send(i)
        except:
            return 0
    return 1


def runpre(name, job="server"):
    global recieved
    #print name
    command1="import dht_functionality_test as t;"
    command2=" t.run("+ job+ ")"
    proc=subprocess.Popen([name + " python"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write(command1)
    proc.stdin.write(command2)
    r = proc.stdout.readline()
    recieved+=1
    return

def run(name, job="server"):
    global counter
    #if (len(sys.argv)>1):
        #job =str(sys.argv[1])
    #else:
        #raise ValueError("Need to enter either job or host name")
    #if (len(sys.argv)>2):
        #filename=str(sys.argv[2])

    #raise Exception ("checkin run")
    if job=="client":
        try:
            test()
        except:
            #print "Sent Packets= "
            return -1
        #print str(2**6)+" Packets sent."
        return 2**6
    else:
        try:
            recieve()
        except:
            #print "Recieved Packets= "+str(counter)
            return counter

        """if (not job=="client"):
            #result=dict({"ip":recieved_ip, "dht":recieved_dht})
            with open ("./test_logs/"+str(table.my_name)+".json", "w+") as f:
                json.dump(result, f, sort_keys=True, indent=4)"""





def check_dht(hosts):
    #hosts=subprocess.call("hosts", shell=True)
    print hosts
    global recieved
    threads=list()
    sleep(5)
    for i in hosts:

        if "_c" in i:
            send=i
        else:
            print i, "i"
            r=(threading.Thread(target=runpre, args=(i,)))
            r.start()
            threads.append(r)
            #test=runpre(name=i)
            #print test

    sent=runpre(name=send, job="client")
    for i in threads:
        i.join()
    if  sent==recieved:
        raise Exception("DHT messages did not arrive properly sent "+str(sent)+" recieved= "+str(recieved))
        return 0
    return

if __name__ == '__main__':
    file_topo="topology.json"
    with open(file_topo, "r") as f:
    		topo=(json.load(f))
    hosts=topo["hosts"]
    check_dht(hosts)
