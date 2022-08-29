import networkx as nx
from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import bind_layers, get_if_addr
import os
import json



from Packet_types import Source_int



class Source_int_sender():
	"""
	"""
	def __init__(self, id):
		self.ip = get_if_addr("eth0")
		print (self.ip)
		with open('topology.json') as f:
			data = json.load(f)
		#print data["switches"]
		self.switches=data["switches"]
		self.hosts=data["hosts"]
		self.links=data["links"]
		self.find_self()
		self.gen_nx_graph_from_topo()

	def gen_nx_graph_from_topo(self):

		"""
		Reconstruct nx graph from topology file.
		"""

		self.g=nx.Graph()
		for l in self.links:
			a= l[0].split("-p")[0]
			b=l[1].split("-p")[0]
			self.g.add_edge(a,b, weight=1)


	def find_self(self):
		"""
		Find own name from ip.
		"""
		for host in self.hosts:
			if self.ip in self.hosts[host]["ip"]:
				self.name= host
				break
		else:
			raise ValueError("Could not find self in in topology file.")


	def find_host_responsible(self, id):
		"""
		return host that is responisble for this id.
		"""
		hosts=get_host_id_pairings(self.hosts.keys(), id_key=True)
		print(hosts)
		for host in hosts:
			if id<host:
				return hosts[host]
		else:
			for host in hosts:
				return hosts[host]

	def get_port_from_hop(self, a, b):
		"""
		return port used for hop from a to b.
		"""
		for l in self.links:
			A= l[0].split("-p")[0]
			B=l[1].split("-p")[0]
			if a==A and b==B:
				return l[0].split("-p")[-1]
			elif a==B and b==A:
				return l[1].split("-p")[-1]
		else:
			raise ValueError("Could not find port for hop")
		

	def send_source_int(self, id, path=None):
		"""
		Send source routed packet with option for in band network telemetry
		"""
		id= self.find_host_responsible(id)
		if path==None:
			path= self.find_path(host)
		ip=ip.split("/")[0]
		addr = socket.gethostbyname(ip)
		pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=3) )
		print(path)
		for i,p in enumerate(path[1:-1]):
			pkt=pkt / Source_int(bottom_of_stack=0, to_metric=0, port= self.get_port_from_hop(path[i],path[i-1]))
		pkt=pkt / Source_int(bottom_of_stack=1, to_metric=0, port= self.get_port_from_hop(path[-2],path[-1]))
		sendp(pkt, iface="eth0")


	def find_path(self, host):
		#TODO will be adapted
		return self.g.shortest_path(self.name, host)[0]

def get_host_id_pairings(hosts, id_key=True):
	"""
	return sorted dict of id: key for hosts unliess id_key==True then key: id
	"""
	to_return=dict()
	for host in hosts:
		id= get_host_id(host)
		if not id==None:
			if id_key==False:
				to_return[host]==id
			else:
				to_return[id]==host
	to_return= {k:v for k,v in sorted(to_return,items(), key=lambda item: item[0])}
	return to_return

def get_host_id(host):
	"""
	return host id as int if not client.
	"""
	id= (host.split("h_")[-1])
	if id=="client":
		return None
	else:
		return int(id)