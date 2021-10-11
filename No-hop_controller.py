#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
from time import sleep
from scapy.all import *
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 './utils/'))

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

import p4runtime_lib.bmv2
#from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

def printCounter(p4info_helper, sw, counter_name, index):
    """
    Reads the specified counter at the specified index from the switch. In our
    program, the index is the tunnel ID. If the index is 0, it will return all
    values from the counter.
    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the counter index (in our case, the tunnel ID)
    """
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            ))

def controller():
    p4info_helper = p4runtime_lib.helper.P4InfoHelper("../../P4_code/compare_dht_forward.p4.p4info.txt")
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0)
    s1.MasterArbitrationUpdate(role=3, election_id = 1)
    for entry in s1.ReadTableEntries():
        print entry


    wait=1
    while (wait==1):

            sleep(1)
            printCounter(p4info_helper, s1, "ThisIngress.c", 0)
            """"try:
                packetin = s1.PacketIn()
            except:
                wait=0
                return
            """
            #print ("recieved packet", packetin)


controller()
