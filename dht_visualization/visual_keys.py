import networkx as nx
import matplotlib.pyplot as plt
import random as random



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

def keys():
    max_id=32
    g=nx.Graph()
    fig = plt.figure()

    host_ids=generate_random_keys()

    connections=[("a","b"),("a","c"),("a","d"),("a","e"),("b","f"), ("b","g"), ("c","f"), ("c","g"), ("d","h"), ("d","i"), ("e","h"), ("e","i"), ("f",host_ids[0]),("f",host_ids[1]),("g",host_ids[2]),("g",host_ids[3]),("h",host_ids[4]), ("h",host_ids[5]),("i",host_ids[6]), ("i",host_ids[7])]
    for i in connections:
        g.add_edge(i[0], i[1], weight=1)


    pos=nx.fruchterman_reingold_layout(g)
    switches= ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
    switch_weight=[0] * len(switches)
    host_weight=[0] * len (host_ids)
    switch_ids=[[]  for _ in range(len(switches))]
    to_print=list()
    for i, h_id  in enumerate(host_ids):

        weight, title, switch_range= find_weight_and_title(host_ids, i , h_id)

        path= nx.dijkstra_path(g, h_id, "a")

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
    for i in to_print:
        plt.title(i[0])
        nx.draw_networkx_edges(g, pos, edge_color="grey", width=2 )
        nx.draw_networkx_edges(g, pos, edgelist=i[1], edge_color="blue", width=2 )
        plt.draw()
        plt.pause(3)

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
