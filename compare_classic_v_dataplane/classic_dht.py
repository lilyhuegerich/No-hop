
import json
import ast
import sys
import os
import random




sys.path.append(
	os.path.join(os.path.dirname(os.path.abspath(__file__)),
				 '../Controller/'))

import Data_Plane_DHT_settings

class table_one_hop():
    """
    Simple baseline implementation of a one hop DHT
    """
	def __init__(self, name="h_R0", file_topo="topology.json"):
		with open(file_topo, "r") as f:
			topo=(json.load(f))
		self.my_name=str(name)
		self.topo=topo
		if (not name in topo["hosts"]):
			print ValueError("name "+name +" not found in topology file")

		self.ip= topo["hosts"][name]["ip"].split("/")[0]
		Range=2** (Data_Plane_DHT_settings.RING_SIZE)

		clients=0
		for i in topo["hosts"]:
			if "_c" in i:
				clients=clients+1
		singal_range= int (Range/(len(topo["hosts"])-clients))
		dif = (Range -(singal_range* (len(topo["hosts"])-clients)))
		self.partition=list()
		spot=0
		for i in (topo["hosts"]):
			if "_c" in i:
				continue
			#print i, type(i)
			self.partition.append(((spot, spot+singal_range+dif), topo["hosts"][i]["ip"].split("/")[0] ))
			spot=singal_range+spot+dif
			dif=0
		print self.partition
	def evaluate(self, id):

		for i in self.partition:

			if (i[0][0]<=id and  id<=i[0][1]):

				if (self.ip in i[1]):

					return 0
				else:
					print "ip to send to "+str(i[1])
					return i[1]
		else:
			raise ValueError ("ID not found in one hop DHT table")



class table():
    """
    Simple baseline implementation of CHORD DHT
    """
	def __init__(self, name="h_R0", file_topo="topology.json", preset_ids=True):
		with open(file_topo, "r") as f:
				topo=(json.load(f))

		self.topo=topo
		if (not name in topo["hosts"]):
			print ValueError("name "+name +" not found in topology file")

		self.my_name=str(name)

		self.preset_ids=preset_ids

		spots=list()
		hosts=0
		if self.preset_ids==True:
			Range=2** (Data_Plane_DHT_settings.RING_SIZE)

			for i in topo["hosts"]:
				if not "_c" in i:
					hosts=hosts+1
			spot=0
			singal_range= int (Range/(hosts))
			dif = (Range -(singal_range* hosts))
			for i in range(0,hosts):
				#print i, type(i)
				spots.append(spot+singal_range+dif)
				spot=singal_range+spot+dif
				dif=0


		hosts=list()

		switches=list()
		print len(topo["links"])
		z=0
		for i in topo["links"]:

			if (not (i[0][0]=="h") or (i[1][0]=="h")):
				continue
			if (i[0][0]=="h" and (not i[0] in (j[0] for j in hosts))):
				h=i[0]
				s=i[1]
			elif (not i[1] in (j[0] for j in hosts)):
				h=i[1]
				s=i[0]
			s=s.split("-p")[0]
			if s in switches:
				print "switches connected to multiple hosts, WARNING for testing this might change results"

			switches.append(s)
			if self.preset_ids==True:  # to be fair to origional chord if we are not useing the same ids as the switches (which we dont for the tree topology we have assigend"good" ids)
				if ("_c" in h):
					continue
				if (h==self.my_name):
					self.my_id=spots[z]
					self.my_name=str(h)


				ip= str(topo["hosts"][h]["ip"]).split("/")[0]
				hosts.append((str(h),spots[z],ip))
				z+=1

			else:


				ID=str((s.split("-p")[0]).split("s")[1])
				ID=ID.split("_")[-1]
				h = str(h)
				ip= str(topo["hosts"][h]["ip"]).split("/")[0]
				if (h==self.my_name):
					self.my_id=str(ID)
					self.my_ip=ip
				if ("_c" in h):
					continue


				hosts.append((h,ID,ip))

		hosts.sort(key=lambda tup: int(tup[1]))
		self.hosts=hosts

		self.table=[]
		for i in range(Data_Plane_DHT_settings.RING_SIZE):
			entry=self.successor((int(self.my_id)+ (2**i)) % (2**Data_Plane_DHT_settings.RING_SIZE))
			#print entry
			self.table.append(entry)


		self.pred=[0,0]
		for i in range(len(self.hosts)):
			if self.hosts[i][1]==self.my_id and str(self.my_name)[0:2] in self.hosts[i][0]:
				if i==0:
					if self.hosts[len(self.hosts)-1][1]==self.my_id:
						continue
					self.pred=self.hosts[len(self.hosts)-1]
				else:
					if self.hosts[i-1][1]==self.my_id:
						continue
					self.pred=self.hosts[i-1]

				break
		else:
			print self.hosts, self.my_name
		#print self.tabl



		print "my id, pred id = ",self.my_id, self.pred[1]


	def successor(self, id):
		print id
		for i in range(len(self.hosts)):
			next=(i+1)% len(self.hosts)
			a=int(self.hosts[i][1])
			b=int(self.hosts[next][1])
			print a, b
			if (a<id) and (id<=b):
				return  self.hosts[next]
			if (a>b and id>a):
				return self.hosts[next]
			if (a>b and id<b and id>=0):
				return self.hosts[next]
			if (a==b):
				return self.hosts[next]
			if (id==b):
				return self.hosts[next]
		else:
			raise ValueError("could not find successor")
	def evaluate(self, id):
		if (int(self.pred[1])<=id and id<=int(self.my_id)):
			return 0
		if (int(self.pred[1])>=int(self.my_id) and id<=64 and id>=int(self.pred[1])):
			return 0
		if (int(self.pred[1])>=int(self.my_id) and id>=0 and id<=int(self.my_id)):
			return 0

		distance=64
		ip=0


		for i in self.table:
			tmp_distance=self.distance(id,int(i[1]))
			if tmp_distance<=distance:
				distance=tmp_distance
				ip=i[2]
		if ip==0:
			raise ValueError("could not evaluate error in fingertable")
		return ip

	def distance(self, id, entry):
		space=64
		entry=int(entry)
		id=int(id)
		if (entry<id):
			return (space-id)+entry
		if (entry>id):
			return (int(entry)-int(id))
		if (entry==id):
			return 0





if  __name__ == '__main__':


	ft=table()
