#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
import json
from time import sleep
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 './utils/'))

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
from No_hop_host import No_hop
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
            print (h)
            if "client" in h:
                continue
            h_ids.append(int( h.split("_")[1]))
        print (sort(h_ids))
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
                if (con_switch in link[0] and "h"==link[1][0] and not link[1]==host):
                    h_pairs.append((str(host), str(link[1]), con_switch))
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
        for i in fail:
            self.rewrite_tables(i)


    def find_responsible(self, id):
        for i, h in enumerate(self.h_ids):
            if i==0 and id>self.h_ids[-1] :
                return h
            if i==0 and id<h:
                return h
            if self.h_ids[i-1]<id and id<=h:
                return h
        else:
            raise ValueError("could not find responsible host in in ids ", self.h_ids, " for the id ", str(id))

    def find_pair_responsible(self, id):
        for i in self.h_pairs:
            if id in i[0]:
                responsible=(i[1], i[2])
                i.remove(i[0])
                return responsible
            if id in i[1]:
                responsible=(i[0], i[2])
                i.remove(i[1])
                return responsible
        else:
            raise ValueError("Both hosts to the same TOR switch failing at the same time is not yet implemented for No-hop-forward.") #TODO

    def rewrite_tables(self, id):
        if self.type==forward:
            self.rewrite_forward_tables(self, id)
        else:
            self.rewrite_rewirte_tables(self, id)

    def rewrite_rewirte_tables(self, id):
        return

    def rewrite_forward_tables(self, id):
        id= self.find_responsible(id)
        responsible= self.find_pair_responsible(id)
        for switch in self.s_l:
            if switch.name==responsible[1]:
                to_change=switch
                break
        else:
            raise ValueError ("could not find responsible switch ", responsible[1], " in " , str([s.name for s in self.s_l]))

        for entry in to_change.s.ReadTableEntries():
            print entry
            if id in entry.range:
                to_change_entry=entry
                break
        raise ValueError("could not find table entry to modify for ID ", id , " and switch ", to_change.name)
        to_change_entry["port"]=new_port #todo
        to_change.s.ModifyTableEntry(t)

        return

    def handle_join(self, join, switch):
        print "Recieved join", str(join), " from switch ", switch.name
        #switch.s.PacketOut() #Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / No_hop(message_type=int(message_type), ID=int(ID), gid=gid, counter=0) / message)

if __name__ == "__main__":
    c= controller()
    c.run()
