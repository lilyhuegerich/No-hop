import networkx as nx
import matplotlib.pyplot as plt
import random as random
import shutil
import json
import sys
import os
import json

rewrite_build_folders=1 #: 1 overwrite existing folder if exists, 0 make new folder
new_folder_prefix="No_hop_Aggregate_"
compiled_p4_program_path="../compare_dht_abstraction"
max_id=32

class network:
    def __init__(self, max_id=32):

        self.switches= ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        self.g=nx.Graph()
        self.max_id=max_id
        self.host_ids=self.generate_random_keys()
        self.connections=[("client", "a"),("a","b"),("a","c"),("a","d"),("a","e"),("b","f"), ("b","g"), ("c","f"), ("c","g"), ("d","h"), ("d","i"), ("e","h"), ("e","i"), ("f",self.host_ids[0]),("f",self.host_ids[1]),("g",self.host_ids[2]),("g",self.host_ids[3]),("h",self.host_ids[4]), ("h",self.host_ids[5]),("i",self.host_ids[6]), ("i",self.host_ids[7])]
        self.used_ports_host,self.used_ports_switch, self.connection_ports= self.define_ports()
        self.folder=self.make_new_folder()

        for i in self.connections:
            self.g.add_edge(i[0], i[1], weight=1)

    def generate_random_keys(self,amount=8):
        """
        Generates <amount> many keys randomly between the values of 0 and <network.max_id> with a distance between ids of atleast 2
        returns a sorted list.
        """
        self.host_ids=list()
        for i in range(8):
            tmp=random.randrange(0,self.max_id)
            while ((tmp in self.host_ids) or ((tmp-1)% self.max_id in self.host_ids) or ( (tmp+1)% self.max_id in self.host_ids)):
                tmp=random.randrange(0,self.max_id)
            self.host_ids.append(tmp)
            self.host_ids.sort()
        return self.host_ids

    def define_ports(self):
        """
        Assign each connection network ports and set corresponding port as taken in corresponding port lists
        """

        used_ports_switch=[[]  for _ in range(len(self.switches))]
        used_ports_host=[[] for _ in range(len(self.host_ids))]
        connection_ports=[[0,0]  for _ in range(len(self.connections))]

        for i, switch in enumerate(self.switches):
            free_port=1
            for c, connection in enumerate(self.connections):
                if connection[0]==switch:
                    used_ports_switch[i].append(free_port)
                    connection_ports[c][0]=free_port
                    free_port+=1
                elif connection[1]==switch:
                    used_ports_switch[i].append(free_port)
                    connection_ports[c][1]=free_port
                    free_port+=1
        for i, host in enumerate(self.host_ids):
            free_port=1
            for c, connection in enumerate(self.connections):
                if connection[0]==host:
                    used_ports_host[i].append(free_port)
                    connection_ports[c][0]=free_port
                    free_port+=1
                elif connection[1]==host:
                    used_ports_host[i].append(free_port)
                    connection_ports[c][1]=free_port
                    free_port+=1

        return used_ports_host, used_ports_switch, connection_ports

    def draw_network(self):
        """
        draws network to pdf in network folder
        """
        fig = plt.figure(figsize=(20, 20))

        pos={"client": (9,6), self.host_ids[0]:(2,2), self.host_ids[1]: (4,2), self.host_ids[2]: (6,2), self.host_ids[3]: (8,2), self.host_ids[4]: (10,2), self.host_ids[5]:(12,2), self.host_ids[6]:(14,2), self.host_ids[7]: (16,2), "a":(9,5), "b": (3,4), "c": (7,4), "d": (11,4), "e": (15,4), "f":(3,3), "g":(7,3), "h":(11,3), "i":(15,3)}
        nx.draw_networkx_nodes(self.g, pos, nodelist=self.host_ids,  node_color="grey") #node_size= host_weight,
        nx.draw_networkx_nodes(self.g, pos, nodelist=["client"], node_color="white") #node_size=switch_weight[0], )
        nx.draw_networkx_nodes(self.g, pos, nodelist=self.switches,  node_color="skyblue") #node_size=switch_weight,)

        for c, connection in enumerate(self.connections):
            nx.draw_networkx_edges(self.g, pos, edgelist=[connection], edge_color="grey")#, width=connection_weight[c])
        plt.draw()
        nx.draw_networkx_labels(self.g, pos,  font_size=30)#labels,
        axis = plt.gca()
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(self.folder+"/network.pdf")

    def make_new_folder(self,folder_name=0):
        """
        Builds empty folder with unused name or rewrites build folder if rewrite_build_folders==1
        """

        path= os.getcwd()
        if  rewrite_build_folders:
            try:
                os.mkdir(path+"/"+new_folder_prefix+str(0))
            except FileExistsError:
                shutil.rmtree(path+"/"+new_folder_prefix+str(0))
                os.mkdir(path+"/"+new_folder_prefix+str(0))
            return path+"/"+new_folder_prefix+str(0)
        if not type(folder_name)==str:
            folder=0
            while (True):
                folder_name=new_folder_prefix+str(folder)
                if not os.path.isdir(folder_name):
                    break
                else:
                    folder+=1

        os.mkdir(path+"/"+folder_name)
        return path+"/"+folder_name

test=network()
test.draw_network()
