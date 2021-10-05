#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
from time import sleep

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2



def controller():
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='logs/s1-p4runtime-requests.txt')
    s1.MasterArbitrationUpdate()
    while (True):
        packetin = s1.PacketIn()
        if packetin.WhichOneof('update')=='packet':
                # print("Received Packet-in\n")
                packet = packetin.packet.payload
                print(packet)

    return

controller()
