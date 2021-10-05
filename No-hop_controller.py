#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
from time import sleep

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 './utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper



def controller():
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            address='127.0.0.1:50051',
            device_id=0
            )
    s1.MasterArbitrationUpdate()
    print(s1.ReadTableEntries())
    try:
        while (True):
            packetin = s1.PacketIn()
            print ("recieved packet", packetin)
            if packetin.WhichOneof('update')=='packet':
                    # print("Received Packet-in\n")
                    packet = packetin.packet.payload
                    print(packet)
    except KeyboardInterrupt:
        return

controller()
