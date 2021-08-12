import shutil
import json
import sys
import os

def make_no_hop_tables(paths, network.switches, switcnetwork.host_ids, network.host_ids, network.connections, network.connection_ports):
    switch_no_hop_tables=[[]  for _ in range(len(network.switches))]
    defined_ids=[[]  for _ in range(len(network.switches))]
    return_entries=[[]  for _ in range(len(network.switches))]
    print (network.connection_ports)
    for path in paths:
        print (path)
        for p in range(len(path)-1):
            for c, connection in enumerate(network.connections):
                if connection[0]==path[p] and connection[1]==path[p+1]:
                    try:
                        a= find_spot(path[p+1], network.switches)
                    except ValueError:  # a is a host
                        continue

                    switch_no_hop_tables[a], defined_ids[a]= make_single_no_hop_table_entry(table= switch_no_hop_tables[a], switch=path[p+1], to=path[p], port=network.connection_ports[c][1], switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches, network.host_ids=network.host_ids, defined_ids= defined_ids[a])
                    #switch_no_hop_tables[a]= fill_rest_entries(table=switch_no_hop_tables[a], switch_indx=a, switch_name=path[p+ 1], b_name= path[p], network.connection_ports=network.connection_ports, network.connections=network.connections, switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches , network.host_ids=network.host_ids)

                    try:
                        b= find_spot(path[p], network.switches)
                    except ValueError: #b is a host
                        break
                    return_entries[b], _= make_single_no_hop_table_entry(table= return_entries[b], switch=path[p], to=path[p+1], port=network.connection_ports[c][0], switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches, ranges=[(0,max_id)], network.host_ids=network.host_ids)
                    break
                if connection[1]==path[p] and connection[0]==path[p+1]:

                    try:
                        a= find_spot(path[p+1], network.switches)
                    except ValueError:
                        continue
                    switch_no_hop_tables[a], defined_ids[a]= make_single_no_hop_table_entry(table= switch_no_hop_tables[a], switch=path[p+1], to=path[p], port=network.connection_ports[c][0], switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches, network.host_ids=network.host_ids, defined_ids=defined_ids[a])
                    #switch_no_hop_tables[a]= fill_rest_entries(table=switch_no_hop_tables[a], switch_indx=a, switch_name=path[p], b_name= path[p+1], network.connection_ports=network.connection_ports, network.connections=network.connections, switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches , network.host_ids=network.host_ids)

                    try:
                        b= find_spot(path[p], network.switches)
                    except ValueError:
                        break
                    return_entries[b], _= make_single_no_hop_table_entry(table= return_entries[b], switch=path[p], to=path[p+1], port=network.connection_ports[c][1], switcnetwork.host_ids=switcnetwork.host_ids, network.switches=network.switches, ranges=[(0,max_id)], network.host_ids=network.host_ids)
                    break
    for r, r_entry in enumerate(return_entries):
        if not (len(r_entry)<1):
            switch_no_hop_tables[r].append(r_entry[0])


    return switch_no_hop_tables
