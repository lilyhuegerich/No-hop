import Data_Plane_DHT
import Data_Plane_DHT_settings
import json
import sys
import os



import shortest_path as shortest_path

""" This file uses the Data_Plane_DHT file to generate different predifened topologies and defines some helper functions for generating topologies"""

class configurationError(Exception):
    pass



class topo_tracker():
    """ Keeps track of generated topology """
    def __init__(self, file_name, file_path="../basic/"):
        self.switches=dict()
        self.links=[]
        self.hosts=dict()
        self.program_name=file_name
        self.file_path=file_path
        self.rewrite_table=0



    def add_switches_to_topo(self, switches, fail=False):
        """ adds generated switches to a already existing topo_tracker
        fail=True is purposfull failing of a link for testing purposes.   """

        for j in switches:
            val=str(j.name)


            if (Data_Plane_DHT_settings.generate_topo_json==1):
                file_name=self.formalize_table(j, fail=fail)
                entry=dict({"runtime_json":file_name, "mac":j.mac})
            else:
                entry=dict({"mac":j.mac})

            self.switches[val]=dict(entry)

    def add_hosts_to_topo(self, rings, amount, client=False, connected_switches=[]):
        for ring in rings:
            for i in range(amount):
                if (not Data_Plane_DHT_settings.bidirectional_connections==1):
                    tmp1_l, tmp2_l= ring.add_host(client=client, switches=connected_switches)
                else:
                     tmp1_l= ring.add_host(client=client, switches=connected_switches)

                for tmp1 in tmp1_l:
                    self.links.append(Data_Plane_DHT.make_string_from_connection(tmp1))
                if (not Data_Plane_DHT_settings.bidirectional_connections==1):
                    for tmp2 in tmp2_l:
                        self.links.append(Data_Plane_DHT.make_string_from_connection(tmp2))

            for i in ring.hosts:
                entry=dict({"ip":i.ip, "mac":i.mac, "commands":i.commands})
                self.hosts[i.name]=entry

        return


    def connect_nodes(self,ring_0_nodes, ring_1_nodes):
        """ connects all nodes in ring 0 to all nodes in ring 1 """
        if (not len(ring_0_nodes)==len(ring_1_nodes)):
            print "must have same amount of nodes from both rings"
            raise ValueError

        for i in range(len(ring_0_nodes)):
            if (not Data_Plane_DHT_settings.bidirectional_connections==1):
                tmp1, tmp2= Data_Plane_DHT.make_bIDirectional_connection(ring_0_nodes[i], ring_1_nodes[i])
            else:
                 tmp1= Data_Plane_DHT.make_bIDirectional_connection(ring_0_nodes[i], ring_1_nodes[i])

            self.links.append(Data_Plane_DHT.make_string_from_connection(tmp1))
            if (not Data_Plane_DHT_settings.bidirectional_connections==1):
                self.links.append(Data_Plane_DHT.make_string_from_connection(tmp2))

    def formalize_table(self, switch, fail=False):
        """ formalize table values to send to the software switch"""
        lpm_table= self.generate_ipv4_lpm_table(switch, fail=fail)
        formal_table=[]
        #print "lpm table", lpm_table

        for i in lpm_table:
            if "/" in i[0]:
                ip=i[0].split("/")
                ip=ip[0]
            else:
                ip=i[0]

            table_entry = dict({
                "table":"ThisIngress.ipv4_lpm",
                "match":{
                    "hdr.ipv4.dstAddr": (ip, i[1])
                },
                "action_name":"ThisIngress.ipv4_forward",
                "action_params":{"dstAddr": i[3],
                                "port": i[2]}})
            formal_table.append(table_entry)
        """
        Now onto formalizing dht entires"

        """

        if ((Data_Plane_DHT_settings.Rewrite_implementation==1) and (not switch.classic==True)) :
            if not self.rewrite_table==0:
                    formal_table=self.rewrite_table
            else:

                range=2** (Data_Plane_DHT_settings.RING_SIZE)-1

                clients=0
                for i in self.hosts:
                    if "_c" in i:
                        clients=clients+1
                singal_range= int (range/(len(self.hosts)-clients))
                dif = (range -(singal_range* (len(self.hosts)-clients)))
                partition=list()
                spot=0
                for i in (self.hosts):
                    if "_c" in i:
                        continue
                    #partition.append((spot, spot+singal_range), i["ip"].split("/")[0] )

                    table_entry = dict({
                        "table":"ThisIngress.finger_table_lookup",
                        "match":{
                            "hdr.dht.group_id": 1,
                            "hdr.dht.id": (spot, spot+singal_range+dif)
                            },
                        "priority": 1,
                        "action_name":"ThisIngress.dht_rewrite",
                        "action_params":{"dht_address": self.hosts[i]["ip"].split("/")[0]}
                        })

                    formal_table.append(table_entry)
                    spot=spot+singal_range+dif
                    dif=0

        elif(not switch.classic==True):

            horizontal, vertical_in, vertical_out= switch.make_tables(fail=fail)
            #print "adding table rules for switch " + str(switch.name)

            keys=[]

            for i in horizontal:
                if not i[1]=="vertical":

                    print "horizontal for switch ", str(switch.name),  i[0][0], i[0][1]
                else:
                    print "vertical for switch ", str(switch.name),  i[0][0], i[0][1]
                for j in range(i[0][0], i[0][1]):
                    if j in keys:
                        continue
                    keys.append(j)

                    if (i[1]=="vertical"):
                        table_entry = dict({
                            "table":"ThisIngress.finger_table_lookup",
                            "match":{
                                "hdr.dht.id": j},
                            "action_name":"ThisIngress.vertical_lookup",
                            "action_params":{}
                                })

                    else:
                        table_entry = dict({
                            "table":"ThisIngress.finger_table_lookup",
                            "match":{
                                "hdr.dht.id": j
                                },
                            "action_name":"ThisIngress.dht_forward",
                            "action_params":{"port": i[1][1]}
                            })
                    formal_table.append(table_entry)

            """Vertical in"""
            keys_i=[]
            for i in vertical_in:
                #print "adding vertical table rules for switch " + str(switch.name) + "with keys 0-",str(i[0])
                for j in range(0,i[0]):
                    if j in keys_i:
                        continue
                    keys_i.append(j)

                    table_entry = dict({
                        "table":"ThisIngress.vertical_lookup_in_table",
                        "match":{
                            "hdr.dht.id": j
                            },
                        "action_name":"ThisIngress.dht_forward",
                        "action_params":{
                            "port": i[1]}
                            })
                    formal_table.append(table_entry)

            """Vertical out"""
            keys_o=[]
            for i in vertical_out:
                for j in range(0, i[0]):
                    if j in keys_o:
                        continue
                    keys_o.append(j)
                    table_entry = dict({
                        "table":"ThisIngress.vertical_lookup_out_table",
                        "match":{
                            "hdr.dht.id": j
                            },
                        "action_name":"ThisIngress.dht_forward",
                        "action_params":{
                            "port": i[1]}
                            })
                    formal_table.append(table_entry)




        if (Data_Plane_DHT_settings.generate_topo_json==1):

                topo_dict=dict({
                                "target":"bmv2",
                                "p4info":(self.file_path+"build/"+self.program_name+".p4.p4info.txt"),
                                "bmv2_json":(self.file_path+"build/"+self.program_name+".json"),
                                "table_entries": formal_table})
                #print topo_dict
                with open(self.file_path+"build/"+str(switch.name)+"P4runtime.json", "w+") as f:
                    json.dump(topo_dict, f, sort_keys=True, indent=4)
                print ("Created JSONs for switch "+str(switch.name)+" with classic = "+str(switch.classic))
                print topo_dict
                return (self.file_path+"build/"+str(switch.name)+"P4runtime.json")

    def generate_ipv4_lpm_table(self, switch, fail=False):
        """ IPv4 tables for comparision of No_hop to classic look up proccess  """
        if Data_Plane_DHT_settings.bidirectional_connections==0:
            print "not yet implemented for non bIDirectional connections/ if not in mininet"
            raise Data_Plane_DHT.SettingError
        lpm_table=[] #3er tuples of ip, prefix, and port
        test=0
        if len(switch.connections_out)==0:
            print "switch "+ str(switch.name) + " has no connections"
            raise configurationError
        if not fail==False:
            if switch==fail[0]:
                fail=fail[1]
                test=1
            elif switch==fail[1]:
                fail=fail[0]
                test=1
            else:
                fail=False
                test=0

        sp=self.paths

        #print sp , "sp"
        for i in self.hosts:
            ip=self.hosts[i]["ip"]
            ip=ip.split("/")[0]
            path=sp.get(switch.name, i)
            if (test==1):
                print path
            if (path==None):
                raise configurationError(i+ " not reachable from "+ switch.name)
            for j in switch.connections_out:
                #print "connections", j.switch_a.name, j.switch_b.name
                if (j.switch_a.name==path[1]):
                    port=j.b_port
                    mac=j.switch_a.mac
                    connect_s=j
                    break
                if (j.switch_b.name==path[1]):
                    port=j.a_port
                    mac=j.switch_b.mac
                    connect_s=j
                    break
            else:
                raise configurationError("could not find link between "+path[0]+" and "+path[1]+" in switches connection list")
            if Data_Plane_DHT_settings.highly_verbose==1:
                print path, (ip,32, port, mac)
            #print path, (ip,32, port, mac)
            if (not fail==False) and (fail==connect_s):
                print "Failing link entries for test", connect_s.name, self.name
            else:
                lpm_table.append((ip,32, port, mac))







        return lpm_table
    def path_finder_ip(self):
        """ wrapper for P4 tutorial shortes path function used in LPM tables"""
         # (hosts * switches)*2


        links=[]

        for i in self.links:
            a=i[0]
            b=i[1]
            if (not a[0]=="h"):
                a=a.split("-p")[0]
            if (not b[0]=="h"):
                b=b.split("-p")[0]
            links.append((a,b))


        self.paths=shortest_path.ShortestPath(links)




    def check_links(self):
        """
        Verfiy correct link configuration , especially checking for duplicates
        """
        links=self.links
        for i in links:
            for j in links:
                if (not j==i):
                    if (j[0]==i[0]):
                        if ("h" not in j[0] and "h" not in i[0]):
                            print j, i , links.index(j), links.index(i)
                            print j[0], i[0], "duplicate!"
                            raise ValueError
                    if (j[1]==i[1]):
                        if ("h" not in j[1] and "h" not in i[1]):
                            print j, i , links.index(j), links.index(i)
                            print j[1], i[1], "duplicate!"
                            raise ValueError
                    if (j[0]==i[1]):
                        if ("h" not in j[0] and "h" not in i[1]):
                            print j, i , links.index(j), links.index(i)
                            print j[0], i[1], "duplicate!"
                            raise ValueError
                    if (j[1]== i[0]):
                        if ("h" not in j[1] and "h" not in i[0]):
                            print j, i , links.index(j), links.index(i)
                            print j[1], i[0], "duplicate!"
                            raise ValueError
    def create_json(self):
        """ print topo object to JSON  """
        if (Data_Plane_DHT_settings.generate_topo_json==1):
            topo_dict=dict(hosts=self.hosts, switches= self.switches, links= self.links)
            with open(self.file_path+"topology.json", "w+") as f:
                json.dump(topo_dict, f, sort_keys=True, indent=4)

        else:
            print "No json created, to change check settings file"

def create_connected_ring(ring_name, level, amount_of_switches, topo, hosts, ip_base=False, switches=[], IDs=[], classic=True):
    """ create a ring of amount_of_switches may switches with hosts many swithes, switches are connected in a ring, returns ring object """
    if (amount_of_switches>hosts):
        print "warning all switches must be connected to hosts or another ring"
    if not ip_base:
        ring_v0_1=Data_Plane_DHT.Ring(ring_name,level=level)
    else:
        ring_v0_1=Data_Plane_DHT.Ring(ring_name,ip_base=ip_base,level=level)
    for i in range(amount_of_switches):
        if i< len (IDs):
            print IDs, i, IDs[i]
            ring_v0_1.add_switch("s", ID=IDs[i], classic=classic)
        else:
            ring_v0_1.add_switch("s", classic=classic)
    if (amount_of_switches>1):
        for i in range(amount_of_switches):
            tmp1=Data_Plane_DHT.connection(ring_v0_1.switches[i], ring_v0_1.switches[((i+1)%(amount_of_switches))])
            topo.links.append(Data_Plane_DHT.make_string_from_connection(tmp1))
            if (amount_of_switches==2):
                break

    topo.add_hosts_to_topo(rings=[ring_v0_1], amount=hosts, connected_switches=switches)

    return ring_v0_1
def quick_test():
    """ simple topology for quick testing"""
    topo=topo_tracker("compare_dht_rewrite", file_path="../compare_classic_v_dataplane/")
    ring=create_connected_ring(ring_name="R",level=0, amount_of_switches=1,topo=topo, hosts=2, classic=False)
    topo.check_links()
    topo.add_hosts_to_topo(rings=[ring], amount=1, client=True)
    topo.path_finder_ip()
    topo.add_switches_to_topo(ring.switches)

    topo.create_json()
    return ring


def test_ring(failover_test=False):
    topo=topo_tracker("compare_dht_rewrite", file_path="../compare_classic_v_dataplane/")
    ring=create_connected_ring(ring_name="R",level=0, amount_of_switches=9,topo=topo, hosts=9)

    topo.check_links()
    topo.add_hosts_to_topo(rings=[ring], amount=1, client=True)
    topo.path_finder_ip()
    topo.add_switches_to_topo(ring.switches)

    topo.create_json()
    return ring

def tree_topo(failover_test=False):
    """
    tree topology for testing classic data center structures
    """
    topo=topo_tracker("compare_dht_rewrite", file_path="../compare_classic_v_dataplane/")
    a=create_connected_ring(ring_name="Ra",level=0, amount_of_switches=1,topo=topo, hosts=0, classic=False)
    #b=create_connected_ring(ring_name="Rb",level=0, amount_of_switches=1,topo=topo, hosts=0)

    c=create_connected_ring(ring_name="Rc",level=1, amount_of_switches=2,topo=topo, hosts=2, switches=[31,31], IDs=[31, 1])
    d=create_connected_ring(ring_name="Rd",level=1, amount_of_switches=2,topo=topo, hosts=2, switches=[1,1], IDs=[31, 1])
    e=create_connected_ring(ring_name="Re",level=1, amount_of_switches=2,topo=topo, hosts=2, switches=[31,31], IDs=[31, 1])
    f=create_connected_ring(ring_name="Rf",level=1, amount_of_switches=2,topo=topo, hosts=2, switches=[1,1], IDs=[31, 1])

    topo.add_hosts_to_topo(rings=[a], amount=1, client=True)
    #topo.links.append(Data_Plane_DHT.make_string_from_connection(Data_Plane_DHT.connection(a.hosts[0] , b.switches[0],host=a.hosts[0])))


    disconect_low_switch=0
    for i in [c,d,e,f]:
        for j in i.switches:
            if len(j.hosts)==0:
                tmp_switch=j
                if i==e and failover_test==True:
                    disconect_low_switch=j
                break
        else:
            raise ValueError("No switch in ring without host connection")
        con=Data_Plane_DHT.connection(a.switches[0], tmp_switch)
        topo.links.append(Data_Plane_DHT.make_string_from_connection(con))
        if failover_test:
            if tmp_switch==disconect_low_switch:
                dis_con=Data_Plane_DHT.make_string_from_connection(con)
        #con=Data_Plane_DHT.connection(b.switches[0], tmp_switch)
        #topo.links.append(Data_Plane_DHT.make_string_from_connection(con))

        tmp_switch=0


    con= Data_Plane_DHT.connection(c.switches[0], d.switches[0])
    topo.links.append(Data_Plane_DHT.make_string_from_connection(con))


    con=Data_Plane_DHT.connection(c.switches[1], d.switches[1])
    topo.links.append(Data_Plane_DHT.make_string_from_connection(con))

    con= Data_Plane_DHT.connection(e.switches[0], f.switches[0])
    topo.links.append(Data_Plane_DHT.make_string_from_connection(con))
    con= Data_Plane_DHT.connection(e.switches[1], f.switches[1])
    topo.links.append(Data_Plane_DHT.make_string_from_connection(con))


    #print topo.links
    topo.path_finder_ip()
    if failover_test==True:
        #print b.switches[0].name, disconect_low_switch.name, "link fail"
        topo.add_switches_to_topo((a.switches+c.switches+d.switches+e.switches+f.switches), fail=(a.switches[0], disconect_low_switch))#b.switches+c.switches+d.switches+e.switches+f.switches), fail=(a.switches[0], disconect_low_switch))
        print "dis_con str", dis_con
        topo.links.remove(dis_con)
    else:
        topo.add_switches_to_topo((a.switches+c.switches+d.switches+e.switches+f.switches))#b.switches+c.switches+d.switches+e.switches+f.switches))

    topo.create_json()
    return
def basic_3_ring(level_zero_amount_of_switches=4, level_one_amount_of_switches=2, outsIDe_nodes=1):
    """
    return ring_v0_1, ring_v1_1, ring_v1_2
    """
    """
    Test topology has one level 0 ring with 4 switches
    two level 1 rings connected each to 2 switches in ring of level 0
    each level one ring has 4 TOR switches

        -all switches are completed connected to all switches of the same ring
    returns 3 rings, ring_v0_1, ring_v1_1 ring_v1_2
    """
    """
    Make ring 1 level 0 with 4 switches
    """


    topo=topo_tracker()
    topo.add_switches_to_json(name_prefixes=["v0_1_s"], amount=level_one_amount_of_switches)
    topo.add_switches_to_json(name_prefixes=["v1_1_s","v1_2_s"],amount=level_zero_amount_of_switches)


    ring_v0_1=create_connected_ring(ring_name="v0_1",level=0, amount_of_switches=level_zero_amount_of_switches,topo=topo)

    ring_v1_1=create_connected_ring(ring_name="v1_1",level=1, ip_base="10.0.1.", amount_of_switches=level_one_amount_of_switches, topo=topo)

    ring_v1_2=create_connected_ring("v1_2",level=1, ip_base="10.0.2.",amount_of_switches=level_one_amount_of_switches, topo=topo)

    topo.add_hosts_to_topo(rings=[ring_v1_1, ring_v1_2], amount=level_one_amount_of_switches)

    topo.add_hosts_to_topo(rings=[ring_v0_1], amount=outsde_nodes)

    """
    Join 2 nodes of ring one to half nodes of ring_v1_1 and two others to half ring_v1_2
    """
    topo.connect_nodes(ring_0_nodes=[ring_v0_1.switches[0],ring_v0_1.switches[2]],
                       ring_1_nodes=[ring_v1_1.switches[0], ring_v1_1.switches[2]])

    topo.connect_nodes(ring_0_nodes=[ring_v0_1.switches[1],ring_v0_1.switches[3]],
                        ring_1_nodes=[ring_v1_1.switches[0], ring_v1_1.switches[2]])

    topo.check_links()

    topo.create_json()

    return ring_v0_1, ring_v1_1, ring_v1_2
