import networkx as nx
import matplotlib.pyplot as plt
import random as random
import shutil
import sys
import os
import Write_Jsons

rewrite_build_folders=1 #: 1 overwrite existing folder if exists, 0 make new folder

node_scalar=500
edge_width=15

class network:
    def __init__(self, max_id=32):
        self.new_folder_prefix="No_hop_Aggregate_"
        self.compiled_p4_program_path="../../P4_code/compare_dht_abstraction"

        self.switches= ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        self.g=nx.Graph()
        self.max_id=max_id
        self.host_ids=self.generate_random_keys()
        self.connections=[("client", "a"),("a","b"),("a","c"),("a","d"),("a","e"),("b","f"), ("b","g"), ("c","f"), ("c","g"), ("d","h"), ("d","i"), ("e","h"), ("e","i"), ("f",self.host_ids[0]),("f",self.host_ids[1]),("g",self.host_ids[2]),("g",self.host_ids[3]),("h",self.host_ids[4]), ("h",self.host_ids[5]),("i",self.host_ids[6]), ("i",self.host_ids[7])]
        for i in self.connections:
            self.g.add_edge(i[0], i[1], weight=1)


        self.used_ports_host,self.used_ports_switch, self.connection_ports= self.define_ports()
        self.folder=self.make_new_folder()
        self.labels, self.reachable=self.find_reachables()




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
        Assign each connection network ports and set corresponding port as taken in corresponding port lists/dicts
        """

        used_ports_switch={}
        used_ports_host={}
        connection_ports=[[0,0]  for _ in range(len(self.connections))]

        for i, switch in enumerate(self.switches):
            free_port=1
            used_ports_switch[switch]=[]
            for c, connection in enumerate(self.connections):
                if connection[0]==switch:
                    used_ports_switch[switch].append(free_port)
                    connection_ports[c][0]=free_port
                    free_port+=1
                elif connection[1]==switch:
                    used_ports_switch[switch].append(free_port)
                    connection_ports[c][1]=free_port
                    free_port+=1
        for i, host in enumerate(self.host_ids):
            free_port=1
            used_ports_host[host]=[]
            for c, connection in enumerate(self.connections):
                if connection[0]==host:
                    used_ports_host[host].append(free_port)
                    connection_ports[c][0]=free_port
                    free_port+=1
                elif connection[1]==host:
                    used_ports_host[host].append(free_port)
                    connection_ports[c][1]=free_port
                    free_port+=1

        return used_ports_host, used_ports_switch, connection_ports

    def draw_network(self):
        """
        draws network to pdf in network folder
        """
        fig = plt.figure(figsize=(20, 20))

        pos={"client": (9,6), self.host_ids[0]:(2,2), self.host_ids[1]: (4,2), self.host_ids[2]: (6,2), self.host_ids[3]: (8,2), self.host_ids[4]: (10,2), self.host_ids[5]:(12,2), self.host_ids[6]:(14,2), self.host_ids[7]: (16,2), "a":(9,5), "b": (3,4), "c": (7,4), "d": (11,4), "e": (15,4), "f":(3,3), "g":(7,3), "h":(11,3), "i":(15,3)}
        for h in self.host_ids:
            nx.draw_networkx_nodes(self.g, pos, nodelist=[h],  node_color="grey", node_size= Write_Jsons.range_size(self.host_range(h))*node_scalar)
        nx.draw_networkx_nodes(self.g, pos, nodelist=["client"], node_color="grey" ,node_size=(self.max_id+1)*node_scalar )
        for s in self.switches:
            nx.draw_networkx_nodes(self.g, pos, nodelist=s,  node_color="skyblue", node_size=Write_Jsons.range_size(self.reachable[s])*node_scalar)

        for c, connection in enumerate(self.connections):
            nx.draw_networkx_edges(self.g, pos, edgelist=[connection], edge_color="grey" ,width=edge_width)
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
                os.mkdir(path+"/"+self.new_folder_prefix+str(0))
            except FileExistsError:
                shutil.rmtree(path+"/"+self.new_folder_prefix+str(0))
                os.mkdir(path+"/"+self.new_folder_prefix+str(0))
            return path+"/"+self.new_folder_prefix+str(0)
        if not type(folder_name)==str:
            folder=0
            while (True):
                folder_name=self.new_folder_prefix+str(folder)
                if not os.path.isdir(self.folder_name):
                    break
                else:
                    folder+=1

        os.mkdir(path+"/"+folder_name)
        return path+"/"+folder_name

    def find_reachables(self):
        """
        Finds the reachable ranges for switches if only traversing the tree downwards
        returns labels, weights. labels a printable version, weights the cleaned ranges.
        """
        traveresed=[]
        for i in self.connections:
            if ("client" in i[0]):
                start=i[1]
                break
            elif ("client" in i[1]):
                start= i[0]
                break

        weights={}
        traveresed.append(start)
        weights[start]=[(0, self.max_id)]
        #weights.append((start,[(0,32)]))
        next_s=list(nx.neighbors(self.g, start))

        while(len(traveresed)< len(self.switches)):

            for s in next_s:
                if s in traveresed or (not s in self.switches):
                    continue
                weight=[]
                for h_s, h in enumerate(self.host_ids):
                    path=nx.dijkstra_path(self.g, h, s )
                    for t in traveresed:
                        if t in path:
                            break
                    else:
                        if h_s==0:
                            weight.append((self.host_ids[-1], h))
                        else:
                            weight.append((self.host_ids[h_s-1], h))
                #weights.append((s, weight))
                weights[s]=weight
            tmp_next=next_s
            next_s=[]
            for s in tmp_next:
                traveresed.append(s)
                for n in list(nx.neighbors(self.g, s)):
                    if n in self.switches:
                        next_s.append(n)

            traveresed = list(dict.fromkeys(traveresed))

        return self.clean_ranges(weights)

    def clean_ranges(self, ranges):
        """
        Takes switch many dict of ranges and cleans each list of ranges to be represented in the minimal amount of ranges.
        returns labels(dict), weights(dict). labels a printable version, weights the cleaned ranges.
        """
        new_ranges={}
        for switch in ranges:


            tmp=list()
            for s in ranges[switch]:
                if (s[0]> s[1]):
                    for i in range(s[0], self.max_id+1):
                        tmp.append(i)
                    for i in range(0, s[1]):
                        tmp.append(i)
                else:
                    for i in range(s[0], s[1]+1):
                        tmp.append(i)

            tmp=list(dict.fromkeys(tmp))
            start=tmp[0]
            new_range=list()


            for i in range(len(tmp)-1):
                if not (tmp[i+1]== tmp[i]+1):
                    if not start==tmp[i]:

                        new_range.append((start, tmp[i]))
                    start=tmp[i+1]
            if not start==tmp[-1]:
                new_range.append((start, tmp[-1]))


            new_ranges[switch]=(new_range)
        labels={}

        for i, switch in enumerate(self.switches):
            if  (len(new_ranges[switch])==1):
                labels[switch]=str(switch)+" \n "+str(new_ranges[switch][0])
            else:
                tmp=str(switch)+" \n "
                for j in new_ranges[switch]:
                    tmp+=str(j)+"\n"
                labels[switch]=tmp

        return labels, new_ranges

    def host_range(self, id):
        """
        Find the range id host is respondible for.
        """

        self.host_ids.sort()
        for i, host in enumerate(self.host_ids):
            if host==id:
                if i==0:
                    return [(self.host_ids[-1], self.max_id), (0, host)]
                else:
                    return [(self.host_ids[i-1], host)]
        else:
            raise ValueError ("no host with ID "+ str(id))

if __name__ == "__main__":
    test=network()
    Write_Jsons.write_build_files(test)
    test.draw_network()
