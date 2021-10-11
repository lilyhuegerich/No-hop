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
    def __init__(self, i, name):
        self.s=p4runtime_lib.bmv2.Bmv2SwitchConnection(
                    name='s'+str(i),
                    address='127.0.0.1:5005'+str(i),
                    device_id=i-1)
        self.join_counter=[0]*max_id
        self.fail_counter=[0]*max_id
        self.name=name
        self.s.MasterArbitrationUpdate(role=3, election_id = 1)

    def check_counters(self, p4info_helper):
        return (self.check_fail(p4info_helper), self.check_join(p4info_helper) )

    def check_fail(self, p4info_helper):
        failed=[]
        for i in range(max_id):
            for response in self.s.ReadCounters(p4info_helper.get_counters_id("ThisIngress.fail"), i):
                for entity in response.entities:
                    counter = entity.counter_entry
                    if not self.fail_counter[i]==counter.data.packet_count:
                        self.fail_counter[i]=counter.data.packet_count
                        failed.append(i)
        return failed

    def check_join(self, p4info_helper):
        joined=[]
        for i in range(max_id):
            for response in self.s.ReadCounters(p4info_helper.get_counters_id("ThisIngress.join"), i):
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
        #print data["switches"]
        switches=data["switches"]

        with open(str(switches["s_a"]["runtime_json"])) as switch_file:
            switch_data=json.load(switch_file)

        if "forward" in str(switch_data["p4info"]):
            self.type="forward"
            self.h_pairs=self.find_host_pairs(data)
        else:
            self.type="rewrite"

        self.h_ids=self.host_ids(data)
        print(self.h_ids)

        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(str(switch_data["p4info"]))
        self.s_l=[]
        self.topo=data
        i=1
        for s in switches:
            self.s_l.append( Switch(i, str(s)))
            i+=1


    def host_ids(self, data):
        h_ids=[]
        for h in data["hosts"]:
            if "client" in h:
                continue
            h_ids.append(int( h.split("_")[1]))
        return h_ids.sort()

    def find_host_pairs(self, data):
        h_pairs=[]
        for host in data["hosts"]:
            con_switch=0
            if "client" in host:
                continue
            if len([h for h in h_pairs if host in h])>0:
                continue
            for link in data["links"]:
                if host in link:
                    con_switch= str(link[(link.index(host)+1)%2]).split("-")[0]
                    break
            else:
                raise ValueError ("Cannot find host ", str(host), " in ", str(data["links"]))
            for link in data["links"]:
                if (con_switch in [str(l).split("-")[0] for l in link]) and ("h" in str(h)[0] for h in link) and (host not in link) :
                    h_pairs.append((str(host), [h for h in link if "h" == str(h)[0]]))
                    break
            else:
                raise ValueError("Could not find pair for ", str(host), " in ", str(data["links"]), "h_pairs ", h_pairs)
        return h_pairs
    def run(self):
        print "Waiting for switch updates......"
        while (True):
                sleep(1)
                for switch in self.s_l:
                    fail, join= switch.check_counters(self.p4info_helper)
                    if not len(fail)==0:
                        self.handle_fail(fail, switch)
                    if not len(join)==0:
                        self.handle_join(join, switch)

    def handle_fail(self, fail, switch):
        print "Recieved fail", str(fail), " from switch ", switch.name
        if self.type=="forward":
            print (self.h_pairs)
    def rewrite_tables():
        return


    def handle_join(self, join, switch):
        print "Recieved join", str(join), " from switch ", switch.name

if __name__ == "__main__":
    c= controller()
    c.run()
