import networkx as nx
import matplotlib.pyplot as plt
import random as random

def keys():
    max_id=32
    g=nx.Graph()
    fig = plt.figure()
    host_ids=list()
    for i in range(8):
        tmp=random.randrange(0,max_id)
        while (tmp in host_ids):
            tmp=random.randrange(0,max_id)
        host_ids.append(tmp)


    connections=[("a","b"),("a","c"),("a","d"),("a","e"),("b","f"), ("b","g"), ("c","f"), ("c","g"), ("d","h"), ("d","i"), ("e","h"), ("e","i"), ("f",host_ids[0]),("f",host_ids[1]),("g",host_ids[2]),("g",host_ids[3]),("h",host_ids[4]), ("h",host_ids[5]),("i",host_ids[6]), ("i",host_ids[7])]


    for i in connections:
        g.add_edge(i[0], i[1], weight=1)


    pos=nx.fruchterman_reingold_layout(g)
    switches= ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
    switch_weight=[0] * len(switches)

    host_weight=[0] * len (host_ids)

    host_ids.sort()

    to_print=list()
    for i, h_id  in enumerate(host_ids):
        weight=0
        if i==0:
            title=("ID's ("+ str(host_ids[-1]) + ", 32) and (0,  " + str( h_id) +")")
            weight=32- host_ids[-1] + h_id
        else:
            title=("ID's from: "+ str(host_ids[i-1])+ " to: " + str(h_id))
            weight=h_id- host_ids[i-1]

        path= nx.dijkstra_path(g, h_id, "a")
        edges=list()
        for i in range(len(path)-1):
            edges.append((path[i], path[i+1]))
            g[path[i]][path[i+1]]['weight']+=.1
        for i, node in enumerate(switches):
            for p in path:
                if node==p:
                    print (weight)
                    switch_weight[i]+=weight
        for i, node in enumerate(host_ids):
            for p in path:
                if node==p:

                    host_weight[i]+=weight

        to_print.append((title, edges))

    for i, h in enumerate(host_weight):
        host_weight[i]= host_weight[i]*75
    for i, h in enumerate(switch_weight):
        switch_weight[i]= h*75
    nx.draw_networkx_nodes(g, pos, nodelist=host_ids, node_size= host_weight,  node_color="grey")
    nx.draw_networkx_nodes(g, pos, nodelist=["a", "b", "c", "d", "e", "f", "g", "h", "i"],  node_size=switch_weight, node_color="skyblue")
    nx.draw_networkx_labels(g, pos, font_size=10)
    for i in to_print:
        plt.title(i[0])
        nx.draw_networkx_edges(g, pos, edge_color="grey", width=2 )
        nx.draw_networkx_edges(g, pos, edgelist=i[1], edge_color="blue", width=2 )


        plt.draw()
        plt.draw()

        plt.pause(3)
    plt.savefig("network.pdf")
    return g, host_ids

def find_responsible(host_ids, id):

    host_ids.sort()
    print(host_ids)
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
