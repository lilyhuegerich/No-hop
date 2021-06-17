import networkx as nx
import matplotlib.pyplot as plt
import random as random

import json
import sys
import os

def generate_random_keys(amount=8, max_id=32):
    host_ids=list()
    for i in range(8):
        tmp=random.randrange(0,max_id)
        while ((tmp in host_ids) or ((tmp-1)% max_id in host_ids) or ( (tmp+1)% max_id in host_ids)):
            tmp=random.randrange(0,max_id)
        host_ids.append(tmp)
        host_ids.sort()
    return host_ids

def add_switch_range(index, switch_ids, switch_range):
    if type(switch_range)==list:
        for i in switch_range:
            switch_ids[index].append(i)
    else:
        switch_ids[index].append(switch_range)
    return switch_ids

def update_traversal_weights(g, path, weight, switch_weight, host_weight, switches, host_ids, switch_ids, switch_range):
    edges=list()
    for i in range(len(path)-1):
        edges.append((path[i], path[i+1]))
        g[path[i]][path[i+1]]['weight']+=.1
    for i, node in enumerate(switches):
        for p in path:
            if node==p:
                switch_weight[i]+=weight
                switch_ids= add_switch_range(i, switch_ids, switch_range)
    for i, node in enumerate(host_ids):
        for p in path:
            if node==p:
                host_weight[i]+=weight

    return g, edges, switch_weight, host_weight, switch_ids

def find_weight_and_title(host_ids, i, h_id):
    switch_range=list()
    weight=0
    if i==0:
        title=("ID's ("+ str(host_ids[-1]) + ", 32) and (0,  " + str( h_id) +")")
        weight=32- host_ids[-1] + h_id
        switch_range.append((host_ids[-1], 32))
        switch_range.append((0, h_id))
    else:
        title=("ID's from: "+ str(host_ids[i-1])+ " to: " + str(h_id))
        weight=h_id- host_ids[i-1]
        switch_range.append((host_ids[i-1], h_id))


    return weight, title, switch_range

def clean_ranges(switch_ids, switches):

    new_switch_ids=list()
    for indx, switch in enumerate(switch_ids):
        #print (switch)
        tmp=list()
        for s in switch:

            for i in range(s[0], s[1]+1):
                tmp.append(i)

        tmp=list(dict.fromkeys(tmp))
        tmp.sort()
        start=tmp[0]
        new_range=list()
        #print (tmp)
        for i in range(len(tmp)-1):
            if not (tmp[i+1]== tmp[i]+1):
                if not start==tmp[i]:
                    new_range.append((start, tmp[i]))
                start=tmp[i+1]
        if not start==tmp[-1]:
            new_range.append((start, tmp[-1]))
        #print(indx, new_range)

        new_switch_ids.append(new_range)
    labels={}
    for i in range(len(switches)):
        if  (len(new_switch_ids[i])==1):
            labels[switches[i]]=new_switch_ids[i][0]
        else:
            labels[switches[i]]=new_switch_ids[i]

    return labels





def scale_weights(host_weight, switch_weight, factor=75):
    for i, h in enumerate(host_weight):
        host_weight[i]= host_weight[i]*factor
    for i, h in enumerate(switch_weight):
        switch_weight[i]= h*factor
    return host_weight, switch_weight


def define_ports(connections, switches, host_ids):

    used_ports_switch=[[]  for _ in range(len(switches))]
    used_ports_host=[[] for _ in range(len(host_ids))]
    connection_ports=[[0,0]  for _ in range(len(connections))]

    for i, switch in enumerate(switches):
        free_port=1
        for c, connection in enumerate(connections):
            if connection[0]==switch:
                used_ports_switch[i].append(free_port)
                connection_ports[c][0]=free_port
                free_port+=1
            elif connection[1]==switch:
                used_ports_switch[i].append(free_port)
                connection_ports[c][1]=free_port
                free_port+=1
    for i, host in enumerate(host_ids):
        free_port=1
        for c, connection in enumerate(connections):
            if connection[0]==host:
                used_ports_host[i].append(free_port)
                connection_ports[c][0]=free_port
                free_port+=1
            elif connection[1]==host:
                used_ports_host[i].append(free_port)
                connection_ports[c][1]=free_port
                free_port+=1

    return used_ports_host, used_ports_switch, connection_ports

def find_switch_id(to_find, switch_ids, switches):
    for s, switch in enumerate(switches):
        if to_find==switch:
            return switch_ids[s]
    else:
        raise ValueError("could not find id range for given switch: "+str(to_find))

def find_spot(entry, list):
    for s, spot in enumerate(list):
        if entry==spot:
            return s
    else:
        raise ValueError("could not find entry: "+ str(entry)+ " in list: "+ str(list))

def host_range(id, host_ids):
    host_ids.sort()
    for i, host in enumerate(host_ids):
        if host==id:
            if i==0:
                return [(host_ids[-1], host)]
            else:
                return [(host_ids[i-1], host)]
    else:
        raise ValueError ("no host with ID "+ str(id))

def make_single_no_hop_table_entry(table, switch, to, port, switch_ids, switches, host_ids, group_id=1, ranges=0):
    if ranges==0:
        try:
            ranges= find_switch_id(to, switch_ids, switches)
        except ValueError:
            ranges= host_range(to, host_ids)
    for r in ranges:
        table_entry = dict({"table":"no_hop_lookup",
        "match":{
            "hdr.dht.group_id": group_id,
            "hdr.dht.id": (r[0], r[1])
            },
        "priority": 1,
        "action_name":"ThisIngress.no_hop_forward",
        "action_params":{"port": port}
        })
        table.append(table_entry)
    return table

def fill_rest_entries(table, switch_indx, switch_name, b_name, connection_ports, connections, switch_ids, switches, host_ids ):
    for c, connection in enumerate(connections):
        if not((connection[0]==switch_name) or (connection[1]==switch_name)):
            continue
        elif ((connection[0]==switch_name) and (not connection[1]==b_name)):
            table=make_single_no_hop_table_entry(table= table, switch=switch_name, to=connection[1], port=connection_ports[c][1], switch_ids=switch_ids, switches=switches, host_ids=host_ids)
        elif ((connection[1]==switch_name) and (not connection[0]==b_name)):
            table=make_single_no_hop_table_entry(table= table, switch=switch_name, to=connection[0], port=connection_ports[c][0], switch_ids=switch_ids, switches=switches, host_ids=host_ids)
    return table

def make_no_hop_tables(paths, switches, switch_ids, host_ids, connections, connection_ports):
    switch_no_hop_tables=[[]  for _ in range(len(switches))]
    return_entries=[[]  for _ in range(len(switches))]
    for path in paths:
        for p in range(len(path)-1):
            for c, connection in enumerate(connections):
                if connection[0]==path[p] and connection[1]==path[p+1]:
                    try:
                        a= find_spot(path[p+1], switches)
                    except ValueError:  # a is a host
                        continue
                    switch_no_hop_tables[a]= make_single_no_hop_table_entry(table= switch_no_hop_tables[a], switch=path[p+1], to=path[p], port=connection_ports[c][1], switch_ids=switch_ids, switches=switches, host_ids=host_ids)
                    switch_no_hop_tables[a]= fill_rest_entries(table=switch_no_hop_tables[a], switch_indx=a, switch_name=path[p+ 1], b_name= path[p], connection_ports=connection_ports, connections=connections, switch_ids=switch_ids, switches=switches , host_ids=host_ids)

                    try:
                        b= find_spot(path[p], switches)
                    except ValueError: #b is a host
                        continue
                    return_entries[b]= make_single_no_hop_table_entry(table= return_entries[b], switch=path[p], to=path[p+1], port=connection_ports[c][0], switch_ids=switch_ids, switches=switches, ranges=[(0,32)], host_ids=host_ids)
                if connection[1]==path[p] and connection[0]==path[p+1]:
                    try:
                        a= find_spot(path[p], switches)
                    except ValueError:
                        continue
                    switch_no_hop_tables[a]= make_single_no_hop_table_entry(table= switch_no_hop_tables[a], switch=path[p], to=path[p+1], port=connection_ports[c][0], switch_ids=switch_ids, switches=switches, host_ids=host_ids)
                    switch_no_hop_tables[a]= fill_rest_entries(table=switch_no_hop_tables[a], switch_indx=a, switch_name=path[p], b_name= path[p+1], connection_ports=connection_ports, connections=connections, switch_ids=switch_ids, switches=switches , host_ids=host_ids)

                    try:
                        b= find_spot(path[p], switches)
                    except ValueError:
                        continue
                    return_entries[b]= make_single_no_hop_table_entry(table= return_entries[b], switch=path[p], to=path[p+1], port=connection_ports[c][0], switch_ids=switch_ids, switches=switches, ranges=[(0,32)], host_ids=host_ids)

    for r, r_entry in enumerate(return_entries):
        if not (len(r_entry)<1):
            switch_no_hop_tables[r].append(r_entry[0])
        else:
            print(switches[r], "has no return entry")
    return switch_no_hop_tables
def keys(gif=False):
    max_id=32
    g=nx.Graph()
    fig = plt.figure()

    host_ids=generate_random_keys()


    switches= ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
    connections=[("a","b"),("a","c"),("a","d"),("a","e"),("b","f"), ("b","g"), ("c","f"), ("c","g"), ("d","h"), ("d","i"), ("e","h"), ("e","i"), ("f",host_ids[0]),("f",host_ids[1]),("g",host_ids[2]),("g",host_ids[3]),("h",host_ids[4]), ("h",host_ids[5]),("i",host_ids[6]), ("i",host_ids[7])]
    used_ports_host,used_ports_switch, connection_ports= define_ports(connections, switches, host_ids)


    for i in connections:
        g.add_edge(i[0], i[1], weight=1)


    pos=nx.fruchterman_reingold_layout(g)

    switch_weight=[0] * len(switches)
    host_weight=[0] * len (host_ids)
    switch_ids=[[]  for _ in range(len(switches))]
    to_print=list()
    paths=list()
    for i, h_id  in enumerate(host_ids):

        weight, title, switch_range= find_weight_and_title(host_ids, i , h_id)

        path= nx.dijkstra_path(g, h_id, "a")
        paths.append(path)
        g, edges, switch_weight, host_weight, switch_ids= update_traversal_weights(g, path, weight, switch_weight, host_weight, switches, host_ids, switch_ids, switch_range)

        to_print.append((title, edges))

    host_weight, switch_weight= scale_weights(host_weight, switch_weight, factor=75)

    labels=clean_ranges(switch_ids, switches)
    for i in host_ids:
        labels[i]=i

    nx.draw_networkx_nodes(g, pos, nodelist=host_ids, node_size= host_weight,  node_color="grey")
    nx.draw_networkx_nodes(g, pos, nodelist=switches,  node_size=switch_weight, node_color="skyblue")
    #nx.draw_networkx_labels(g, pos, font_size=10)
    nx.draw_networkx_labels(g, pos, labels, font_size=8)
    if (gif):
        for i in to_print:
            plt.title(i[0])
            nx.draw_networkx_edges(g, pos, edge_color="grey", width=2 )
            nx.draw_networkx_edges(g, pos, edgelist=i[1], edge_color="blue", width=2 )
            plt.draw()
            plt.pause(3)

    nx.draw_networkx_edges(g, pos, edge_color="grey", width=2 )
    plt.draw()

    switch_no_hop_tables= make_no_hop_tables(paths, switches, switch_ids, host_ids, connections, connection_ports)
    #fill and write jsons

    #create folder and add pickled objects as well as final jsons
    print (paths)
    plt.savefig("network.pdf")
    return g, host_ids




def find_responsible(host_ids, id):

    host_ids.sort()
    #print(host_ids)
    for i, h_id in enumerate(host_ids):
        if i==0:
            if id<=h_id or id>host_ids[-1]:
                respondible=h_id
                break
        elif id<=h_id and id>host_ids[i-1]:
            respondible=h_id
            break
    else:
        raise ValueError("could not find respondible")
    #print ("Host: ", h_id, "respondible for id: ", id)

    return h_id

def find_paths(G, host_ids, id):
    respondible=find_responsible(host_ids, id)

    return nx.dijkstra_path(G, respondible, "a")




G,host_ids=keys()
#find_paths(G, host_ids, 27 )
