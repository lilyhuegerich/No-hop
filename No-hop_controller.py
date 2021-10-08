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


def controller():
    p4info_helper = p4runtime_lib.helper.P4InfoHelper("../../P4_code/compare_dht_forward.p4.p4info.txt")
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0)
    s1.MasterArbitrationUpdate(role=3, election_id = 1)
    for entry in s1.ReadTableEntries():
        print entry
    mc_group_entry = p4info_helper.buildMCEntry(
            mc_group_id = 1,
            replicas = {
                1:1,
                2:2,
                3:3
            })
    s1.WritePRE(mc_group = mc_group_entry)
    print "Installed mgrp on s1."

    wait=1
    while (wait==1):
            print ("waiting to recieve packet from switch")
            try:
                packetin = s1.PacketIn()
            except:
                wait=0
                return

            print ("recieved packet", packetin)
            if packetin.WhichOneof('update')=='packet':
                    # print("Received Packet-in\n")
                    packet = packetin.packet.payload
                    print(packet)


controller()
