#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
import json
from pprint import pprint
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
    """
    Controller Class for switches
    """
    def __init__(self, i, name, switches):
        self.s=p4runtime_lib.bmv2.Bmv2SwitchConnection(
                    name='s'+str(i),
                    address='127.0.0.1:5005'+str(i),
                    device_id=i-1)
        self.join_counter=[0]*max_id
        self.fail_counter=[0]*max_id
        self.name=name
        with open (str(switches[name]["runtime_json"])) as f:
            self.runtime_json=json.load(f)

        self.s.MasterArbitrationUpdate(role=3, election_id = 1)

    def check_counters(self, p4info_helper):
        """
        Check to see if fail and join counters have changed (If a new fail or join was noticed by a switch)
        """
        return (self.check_fail(p4info_helper), self.check_join(p4info_helper) )

    def check_fail(self, p4info_helper):
        """
        Check to see if fail counters have changed (If a new fail was noticed by a switch)
        """
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
        """
        Check to see if join counters have changed (If a new join was noticed by a switch)
        """
        joined=[]
        for i in range(max_id):
            for response in self.s.ReadCounters(p4info_helper.get_counters_id("ThisIngress.join"), i):
                for entity in response.entities:
                    counter = entity.counter_entry
                    if not self.join_counter[i]==counter.data.packet_count:
                        self.join_counter[i]=counter.data.packet_count
                        joined.append(i)
        return joined
    def delete_tables(self):
        """
        Delete all table entries of a switch
        """
        i=0
        for entry in self.s.ReadTableEntries():
            #pprint(dir(entry))
            for e in entry.entities:
                print e.table_entry , i
                print dir(e)
                self.s.DeleteTableEntry(e.table_entry)
                i+=1
        for entry in  self.s.ReadTableEntries():
            print (entry)
class controller:
    """
    Controller class
    """
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

        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(str(switch_data["p4info"]))
        self.s_l=[]
        self.topo=data
        i=1
        for s in switches:
            self.s_l.append( Switch(i, s, switches))
            i+=1


    def host_ids(self, data):
        """
        From the topology file finds the ids of the hosts, returns an ordered list of ints
        """
        h_ids=[]
        for h in data["hosts"]:
            if "client" in h:
                continue
            h_ids.append(int( h.split("_")[1]))
        h_ids.sort()
        return h_ids

    def find_host_pairs(self, data):
        """
        Only relevant for no-hop_forward in a tree structure, sort hosts by witch TOR switch they are connected to.
        """
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
                    h_pairs.append([str(host), str(link[1]), con_switch])
                    break
            else:
                raise ValueError("Could not find pair for ", str(host), " in ", str(data["links"]), "h_pairs ", h_pairs)
        return h_pairs


    def run(self):
        """
        Start controller
        """
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
        """
        respond to fail message
        """
        print "Recieved fail", str(fail), " from switch ", switch.name
        for i in fail:
            self.rewrite_tables(i)


    def find_responsible(self, id):
        """
        Returns which host ID is responsible for id
        """
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
        """
        Returns which TOR and the attatched hosts proccess the id (again only for No-hop-forward in a tree topology)
        """
        for i in self.h_pairs:
            if str(id) in i[0]:
                responsible=[i[1], i[2]]
                i.remove(i[0])
                return responsible
            if str(id) in i[1]:
                responsible=[i[0], i[2]]
                i.remove(i[1])
                return responsible
        else:
            raise ValueError("Both hosts to the same TOR switch failing at the same time is not yet implemented for No-hop-forward.") #TODO

    def rewrite_tables(self, id):
        """
        Update tables so that they do not forward to failed hosts.
        """
        if self.type=="forward":
            self.rewrite_forward_tables(id)
        else:
            self.rewrite_rewirte_tables(id)

    def rewrite_rewirte_tables(self, id):
        """
        Rewrite tables if network of type rewrite
        """
        return

    def rewrite_forward_tables(self, id):
        """
        Rewrite tables if network of type forward
        """
        id= self.find_responsible(id)
        responsible= self.find_pair_responsible(id)
        for switch in self.s_l:
            if switch.name==responsible[1]:
                to_change=switch
                break
        else:
            raise ValueError ("could not find responsible switch ", responsible[1], " in " , str([s.name for s in self.s_l]))

        for entry in to_change.runtime_json["table_entries"]:
            #print ((int(entry["match"]["hdr.dht.id"][0]),  int(entry["match"]["hdr.dht.id"][1]), id), entry["action_name"])
            if (str(entry["action_name"]) ==  "ThisIngress.no_hop_forward") and (int(entry["match"]["hdr.dht.id"][0])<id) and  (int(entry["match"]["hdr.dht.id"][1])>=id):
                new_entry=entry
                break
        else:
            raise ValueError("could not find table entry to modify for ID ", id , " and switch ", to_change.name)
        #TODO change outgoing port

        table_name = new_entry['table']
        match_fields = new_entry.get('match')
        action_name = new_entry['action_name']
        default_action = new_entry.get('default_action')
        action_params = new_entry['action_params']
        priority = new_entry.get('priority')

        table_entry = self.p4info_helper.buildTableEntry(
            table_name=table_name,
            match_fields=match_fields,
            default_action=default_action,
            action_name=action_name,
            action_params=action_params,
            priority=priority)
        print (table_entry)
        to_change.delete_tables()
        for entry in to_change.s.ReadTableEntries():
            for e in entry.entities:
                print e.table_entry , i
                print dir(e)
                self.s.DeleteTableEntry(e.table_entry)
                break

        to_change.s.DeleteTableEntry(table_entry)

        return

    def handle_join(self, join, switch):
        """
        respond to join message
        """
        print "Recieved join", str(join), " from switch ", switch.name
        #switch.s.PacketOut() #Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / No_hop(message_type=int(message_type), ID=int(ID), gid=gid, counter=0) / message)

if __name__ == "__main__":
    c= controller()
    c.run()
