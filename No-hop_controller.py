#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
import json
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
max_id=32

class Switch:
    def __init__(self, i):
        self.s=p4runtime_lib.bmv2.Bmv2SwitchConnection(
                    name='s'+str(i),
                    address='127.0.0.1:5005'+str(i),
                    device_id=i-1)
        self.join_counter=[0]*max_id
        self.fail_counter=[0]*max_id
        self.s.MasterArbitrationUpdate(role=3, election_id = 1)

    def check_counters(self, p4info_helper):
        return (self.check_fail(p4info_helper), self.check_join(p4info_helper) )

    def check_fail(self, p4info_helper):
        failed=[]
        for i in range(max_id):
            for response in self.s.ReadCounters(p4info_helper.get_counters_id(ThisIngress.fail), i):
                for entity in response.entities:
                    counter = entity.counter_entry
                    if not self.fail_counter[i]==counter.data.packet_count:
                        self.fail_counter[i]=counter.data.packet_count
                        failed.append(i)
        return failed

    def check_join(self, p4info_helper):
        joined=[]
        for i in range(max_id):
            for response in self.s.ReadCounters(p4info_helper.get_counters_id(ThisIngress.join), i):
                for entity in response.entities:
                    counter = entity.counter_entry
                    if not self.join_counter[i]==counter.data.packet_count:
                        self.join_counter[i]=counter.data.packet_count
                        joined.append(i)
        return joined
    def read_tables(self):
        for entry in self.s.ReadTableEntries():
            print entry

class controller:
    def __init__(self):
        with open('topology.json') as f:
            data = json.load(f)
        print data["switches"]
        switches=data["switches"]

        with open(str(switches["s_a"]["runtime_json"])) as switch_file:
            switch_data=json.load(switch_file)
        print (switch_data["p4info"])
        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(str(switch_data["p4info"]))
        self.s_l=[]
        self.topo=data
        i=1
        for _ in switches:
            self.s_l.append( Switch(i))
            i+=1



    def run(self):
        while (True):
                sleep(1)
                for switch in self.s_l:
                    fail, join= switch.check_counters(self.p4info_helper)
                    if not len(fail)==0:
                        handle_fail(fail)
                    if not len(join)==0:
                        handle_join(join)

    def handle_fail(self, fail):
        print "Recieved fail", str(fail)
    def handle_join(self, join):
        print "Recieved join", str(join)

if __name__ == "__main__":
    c= controller()
    c.run()
