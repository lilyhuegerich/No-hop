import shutil
import json
import sys
import os


def write_topology_file(network):
    links=formalize_connections(connections, connection_ports, switches, host_ids)
    switches_formal= formalize_switches(switches,folder_name)
    topo_dict=dict(hosts=network.host_ids, switches= switches_formal, links= links)
    with open(network.folder_name+"/topology.json", "w+") as f:
        json.dump(topo_dict, f, sort_keys=False, indent=4)

def make_no_hop_tables(network):
    """
    For all switches generate no_hop tables as dictionaries
    returns dict: {switch: switch_no_hop_table}
    """

    no_hop_tables={}
    for switch in network.switches:
        no_hop_tables[switch]=make_no_hop_table(network, switch)
    return no_hop_tables

def make_no_hop_table(network , switch):
    """
    For switch, generate no_hop table
    returns list of entries
    """

    connected=switch_connections(network, switch)
    no_hop_table={}
    up_tree=0
    for i in connected:
        if i in no_hop_table:
            continue
        elif i in network.host_ids:
            no_hop_table[i]=(make_single_no_hop_table_entry(port=connected[i]), range=network.host_range(i)))
        elif (range_size(network.reachable[switch])< range_size(network.reachable[i])):
            """
            The last range match for switches, sends the packet back up the tree
            """
            up_tree=(make_single_no_hop_table_entry(port=connected[i]), range=(0, network.max_id+1)))
        else:
            for j in connected:
                if not j==i:
                    if network.reachable[i]==network.reachable[j]:
                        if (len(network.reachable[i]==2)):
                            """
                            to minimize range fields, if range is already split just use the already given split point
                            """
                            no_hop_table[i]=(make_single_no_hop_table_entry(port=connected[i]), range=(network.reachable[i][0][0], network.reachable[i][0][1]))
                            no_hop_table[j]=(make_single_no_hop_table_entry(port=connected[j]), range=(network.reachable[i][1][0], network.reachable[i][1][1]))

                        elif (len(network.reachable[i]==1)):
                            """
                            split range
                            """
                            split_point=0
                            total=0
                            for k in network.reachable[i]:
                                total+= k[1]-k[0]

                            split_point=total/2
                            no_hop_table[i]=(make_single_no_hop_table_entry(port=connected[i]), range=(network.reachable[i][0][0], network.reachable[i][0][0]+ split_point))
                            no_hop_table[j]=(make_single_no_hop_table_entry(port=connected[j]), range=(network.reachable[i][0][0] +split_point, network.reachable[i][0][1]))
                        else:
                            raise ValueError ("Either more than two ranges were found for reachable or there was a mistake while computing reachables")

    no_hop_table=list(no_hop_table.values())
    if not up_tree==0:
        no_hop_tables[switch].append(up_tree)
    return no_hop_table

def range_size(range_list):
    """
    calculate total size of range_list
    """
    r_s=0
    for r in range_list:
        r_s+= r[1]- r[0]
    return r_s

def make_single_no_hop_table_entry ( port, range, group_id=1):
    """
    Make a single no hop table entry that sends range(tuple) out of port (int) and matches to group_id(int, default=1)
    returns entry as dict
    """

    table_entry = dict({"table":"ThisIngress.no_hop_lookup",
    "match":{
        "hdr.dht.group_id": group_id,
        "hdr.dht.id": (r[0], r[1])
        },
    "priority": 1,
    "action_name":"ThisIngress.no_hop_forward",
    "action_params":{"port": port}
    })
    return table_entry



def switch_connections(network, switch):
    """
    Return a dictionary {connection target: Outgoing port} for all connections that switch is in
    """
    connected={}
    for c_i, connection in enumerate(network.connections):
        if connection[0]==switch:
            connected[connection[1]]=network.connection_ports[c_i][0]
        elif connection[1]==switch:
            connected[connection[0]]=network.connection_ports[c_i][1]
    return connected

def formalize_switch(switch, s):
    """
    Create single entry for a switch in topology.json
    """
    entry= {
        "mac": "08:00:00:00:01:"+str(s),
        "runtime_json": "./build/"+switch+"P4runtime.json"
    }
    return entry

def formalize_switches(switches):
    """
    Create all entries for the switches in the topology.json
    """"

    switches_formal=dict()
    for s, switch in enumerate(switches):
        switches_formal["s_"+switch]=formalize_switch(switch, s)
    return switches_formal

def formalize_connection_names(network):
    """
    Bring connections into a printable/ readable form for mininet
    """
    new_connections=[[0,0] for _ in range(len(network.connections))]
    for c, connection in enumerate(network.connections):
        if connection[0] in network.switches:
            new_connections[c][0]="s_"+str(connection[0])
        elif connection[0] in network.host_ids:
            new_connections[c][0]="h_"+str(connection[0])
        else:
            new_connections[c][0]="h_client"
        if connection[1] in network.switches:
            new_connections[c][1]="s_"+str(connection[1])
        elif connection[1] in network.host_ids:
            new_connections[c][1]="h_"+str(connection[1])
        else:
            new_connections[c][1]="h_client"
    return new_connections

def formalize_connections(network):
    """
    Prepare connections for printing to JSON
    """
    
    links=list()
    connections=formalize_connection_names(network)
    for c, connection in enumerate(connections):
        if connection[0][0]=="h":
            links.append([str(connection[0]), str(connection[1])+"-p"+str(network.connection_ports[c][1])])
        elif connection[1][0]=="h":
            links.append([str(connection[0])+"-p"+str(network.connection_ports[c][0]), str(connection[1])])
        else:
            links.append([str(connection[0])+"-p"+str(network.connection_ports[c][0]), str(connection[1])+"-p"+str(connection_ports[c][1])])
    return links
