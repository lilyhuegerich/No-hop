#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
#import p4runtime_sh.shell as sh
import json
from pprint import pprint
from time import sleep
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import sendp, send, srp1, sniff
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 './utils/'))

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper
from No_hop_host import No_hop

import threading

max_id=32


MODE="PASSIVE" #"ACTIVE" checks fail and join regesters periodically, "PASSIVE" waits for fail or join messages from switches

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
        self.listened_to_by_thread=None #Thread that the controlller is listening on
        self.controller_listening=False

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
                print (e.table_entry , i)
                print (dir(e))
                self.s.DeleteTableEntry(e.table_entry)
                i+=1
        for entry in  self.s.ReadTableEntries():
            print (entry)
    def read_tables(self):
        """
        read all table entries of a switch
        """
        i=0
        for entry in self.s.ReadTableEntries():
            #pprint(dir(entry))
            for e in entry.entities:
                print (e.table_entry , i)
                i+=1

    def write_table(self, table_entry):
        """
        Write table entry to switch, pass exceptions
        """

        try:
            self.s.WriteTableEntry(table_entry)
            print ("Added table entry")# ", table_entry)
        except Exception as ex:
            print (ex, self.name)
            pass
        return

    def listened_to(self):
        print("Controller listening", self.name)
        while self.controller_listening:
            try:
                r=self.s.PacketIn(timoeut=1)
                packet=Ether(r.packet.payload)
                if "IP" in packet:
                    if packet["IP"].proto==2:
                        pkt= packet["No_hop"]
                        if pkt.message_type==2:
                            self.controller_listening.handle_fail([pkt.ID], self)
                        elif pkt.message_type==3:
                            self.controller_listening.handle_join([pkt.ID], self)
                        
            except:
                break

        return


class controller():
    """
    Controller class
    """
    def __init__(self, verbose=True):
        with open('topology.json') as f:
            data = json.load(f)
        #print data["switches"]
        switches=data["switches"]

        with open(str(switches["s_a"]["runtime_json"])) as switch_file:
            switch_data=json.load(switch_file)
        self.verbose=verbose
        if "forward" in str(switch_data["p4info"]):
            self.type="forward"
            self.h_pairs=self.find_host_pairs(data)
        else:
            self.type="rewrite"

        self.h_ids=self.host_ids(data)
        self.p4info_helper = p4runtime_lib.helper.P4InfoHelper(str(switch_data["p4info"]))

        with open(str(switch_data["p4info"])) as p4_info:
            p4_info_data=p4_info.readlines()

        for i, entry in enumerate(p4_info_data):
            if "ThisIngress.no_hop_lookup" in entry:
                self.no_hop_table_id=p4_info_data[i-1].split(":")[-1][:-1].strip()
                break
        else:
            raise ValueError("Could not find Table id of No_hop-lookup.")
        
        self.running=True

        self.s_l=[]
        self.topo=data

        for s in switches:
            i = int(self.topo["switches"][s]["mac"].split(":")[-1])+1
            if self.verbose:
                print ("switch ", s, i)
            self.s_l.append( Switch(i, s, switches))

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
            port_a=-1
            port_b=-1
            if "client" in host:
                continue
            if len([h for h in h_pairs if host in h])>0:
                continue
            for link in data["links"]:
                if host in link:
                    con_switch= str(link[(link.index(host)+1)%2]).split("-")[0]
                    port_a=int(str(link[(link.index(host)+1)%2]).split("-p")[1])
                    break
            #else:
            #   print("raise ValueError ("Cannot find host ", str(host), " in ", str(data["links"]))")
            for link in data["links"]:
                if (con_switch in link[0] and "h"==link[1][0] and not link[1]==host):
                    port_b=int(str(link[0]).split("-p")[1])
                    h_pairs.append([str(host), str(link[1]), con_switch, (port_a, port_b)])
                    break
            else:
                raise ValueError("Could not find pair for ", str(host), " in ", str(data["links"]), "h_pairs ", h_pairs)
        return h_pairs

    def listen(self, s):
        s.controller_listening=self
        s.listened_to_by_thread=threading.Thread(target=s.listened_to)
        s.listened_to_by_thread.start()
        

    def end_listening(self, s):
        s.controller_listening=False
        s.listened_to_by_thread.join()
    
    def run(self):
        """
        Start controller
        """
        import time
        print ("Waiting for switch updates......")
        iface = 'eth3'

        #print(sniff(prn= lambda x:x.summary()))

        
        try:
            
            if MODE=="ACTIVE":
                while (True):
                    for switch in self.s_l:
                        fail, join= switch.check_counters(self.p4info_helper)
                        if not len(fail)==0:
                            self.handle_fail(fail, switch)
                        if not len(join)==0:
                            self.handle_join(join, switch)

            elif MODE=="PASSIVE":
                for s in self.s_l:
                    self.listen(s)
                    
            else:
                raise ValueError("mode not known"+ str(MODE))

        except KeyboardInterrupt:
            
            if MODE=="PASSIVE":
                for s in self.s_l:
                    self.end_listening(s)
    
            

       
    def handle_fail(self, fail, switch):
        """
        respond to fail message
        """
        print ("Recieved fail", str(fail), " from switch ", switch.name)
        for i in fail:
            self.rewrite_tables(i, switch)


    def find_responsible(self, id):
        """
        Returns which host ID is responsible for id
        """

        for i, h in enumerate(self.h_ids):
            if i==0 and id>self.h_ids[-1] :
                if self.verbose:
                    print ("responsible for id ", id , " is ", h)
                return h
            if i==0 and id<=h:
                if self.verbose:
                    print ("responsible for id ", id , " is ", h)
                return h
            if self.h_ids[i-1]<id and id<=h:
                if self.verbose:
                    print ("responsible for id ", id , " is ", h)
                return h
        else:
            raise ValueError("could not find responsible host in in ids ", self.h_ids, " for the id ", str(id))

    def find_pair_responsible(self, id):
        """
        Returns which TOR and the attatched hosts proccess the id (again only for No-hop-forward in a tree topology)
        """
        #TODO remove failed hosts
        for i in self.h_pairs:
            if str(id) in i[0].split("_")[1]:
                responsible=[i[1], i[2], i[3][1]]
                if self.verbose:
                    print ("responsible for id ", id , " is switch  ", i[2], " new port : ", i[3][0])
                return responsible
            if str(id) == i[1].split("_")[1]:
                responsible=[i[0], i[2], i[3][0]]
                if self.verbose:
                    print ("responsible for id ", id , " is switch  ", i[2], " new port : ", i[3][1])
                return responsible
        else:
            raise ValueError("Both hosts to the same TOR switch failing at the same time is not yet implemented for No-hop-forward.") #TODO

    def rewrite_tables(self, id, switch=0):
        """
        Update tables so that they do not forward to failed hosts.
        """
        if self.type=="forward":
            self.rewrite_forward_tables(id)
        else:
            self.rewrite_rewirte_tables(id, switch)
        #TODO remove old id
    def rewrite_rewirte_tables(self, id, switch):
        """
        Rewrite tables if network of type rewrite
        """

        id=self.find_responsible(id)
        failed_ip=self.find_host_ip(id)
        succesor_id=self.succesor(id)
        succesor_ip= self.find_host_ip(succesor_id)

        for entry in to_change.s.ReadTableEntries():
            #pprint(dir(entry))
            for e in entry.entities:
                if e.table_id==self.no_hop_table_id:
                    print("TODO")
    def succesor(self, id):
        """
        Return the next switch following the switch with id: id
        """
        for i, host in enumerate(self.host_ids):
            if host==id:
                if i==0:
                    if self.verbose:
                        print ("successor to id ", id, " is ", self.host_ids[-1])
                    return self.host_ids[-1]
                else:
                    if self.verbose:
                        print ("successor to id ", id, " is ", self.host_ids[i-1])
                    return self.host_ids[i-1]
        else:
            raise ValueError("Could not find id ", id, " in ", str(self.host_ids))



    def find_host_ip(self, id):
        """
        Return the ip of the host with id, id
        """
        for host in self.topo["hosts"]:
            if str(id)==str(host).split("_")[1]:
                return self.topo[host]["ip"]
        else:
            raise ValueError("Could not find host with id ", id, " in ", str(self.topo["hosts"]))
    def rewrite_forward_tables(self, id):
        """
        Rewrite tables if network of type forward
        """
        id= self.find_responsible(id)
        responsible= self.find_pair_responsible(id)
        for switch in self.s_l:
            if switch.name==responsible[1]:
                to_change=switch
                if self.verbose:
                    print ("to_change: ", to_change.name)
                new_port=responsible[2]
                break
        else:
            raise ValueError ("could not find responsible switch ", responsible[1], " in " , str([s.name for s in self.s_l]))
        new_entry=[]
        found=0
        for index, entry in enumerate(to_change.runtime_json["table_entries"]):
            #print ((int(entry["match"]["hdr.dht.id"][0]),  int(entry["match"]["hdr.dht.id"][1]), id), entry["action_name"])

            if (str(entry["action_name"]) ==  "ThisIngress.no_hop_forward"):
                #print (entry)
                if  (int(entry["match"]["hdr.dht.id"][0])<id) and  (int(entry["match"]["hdr.dht.id"][1])>=id) and not (int(entry["match"]["hdr.dht.id"][1])>=32 and int(entry["match"]["hdr.dht.id"][0])<=0):
                    new_entry.append(entry)
                    found=1

        if found==0:
            raise ValueError("could not find table entry to modify for ID ", id , " and switch ", to_change.name)

        #print (table_entry
        found=0
        for entry in to_change.s.ReadTableEntries():
            #pprint(dir(entry))
            print("here")
            for e in entry.entities:
                print("here2")
                #print (e.table_entry.table_id, self.no_hop_table_id)
                if (str(e.table_entry.table_id)== str(self.no_hop_table_id)):
                    print("table")
                    if str(new_entry[0]["action_params"]["port"]) in str(e.table_entry.action.action.params._values).split("\0")[-1]:
                        print ("deleting table entry ")#,  e.table_entry)
                        if self.verbose:
                            print (e.table_entry)
                        print("here2.5")

                        to_change.s.DeleteTableEntry(e.table_entry)
                        found=1
                        print("here3")
                        #TODO test if multiple range mathes fit the host work
        print("here4")
        if found==0: #TODO uncomment
            raise ValueError("Could not find entry to delete")
        self.write_new_forward_tables(new_entry, new_port, to_change)
        print("finished")

    def write_new_forward_tables(self, entries, new_port, to_change):
        """
        Write new entries with adjusted port to to_change
        """
        for entry in entries:
            entry["action_params"]["port"]=new_port
            table_name = entry['table']
            match_fields = entry.get('match')
            action_name = entry['action_name']
            default_action = entry.get('default_action')
            action_params = entry['action_params']
            priority = entry.get('priority')

            table_entry = self.p4info_helper.buildTableEntry(
                table_name=table_name,
                match_fields=match_fields,
                default_action=default_action,
                action_name=action_name,
                action_params=action_params,
                priority=priority)

            to_change.write_table(table_entry)

    def handle_join(self, join, switch):
        """
        respond to join message, currently only a stub since only in mininet
        """
        print ("Recieved join", str(join), " from switch ", switch.name)
        #switch.s.PacketOut() #Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / No_hop(message_type=int(message_type), ID=int(ID), gid=gid, counter=0) / message)

if __name__ == "__main__":
    c= controller(verbose=False)
    c.run()
