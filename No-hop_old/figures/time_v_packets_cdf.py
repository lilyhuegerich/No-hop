import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add

logs= (glob.glob("../compare_classic_v_dataplane/test_logs/tree_time_1000/*.json"))

ring_logs=(glob.glob("../compare_classic_v_dataplane/test_logs/time_ring/*.json"))

i_sum=0
d_sum=0
d_sum_ring=0
i_sum_ring=0


results=list()
dht_list=list()
results_ring=list()
dht_list_ring=list()
for log in logs:
    with open(log, "r") as l:
        tests=json.load(l)
    test=tests["ip"]

    for i in test:
        counter=i.split("*")[0]
        counter=-1*float(counter)
        #print (counter, i_sum)
        i_sum+=counter
        results.append(counter)
    test=tests["dht"]

    for i in test:

        counter=-1*float(i)
        d_sum+=counter
        dht_list.append(counter)
print (len(results), i_sum, "classic", i_sum/len(results))
print (len(dht_list), d_sum ,"dht", d_sum/len(dht_list))
for log in ring_logs:
    with open(log, "r") as l:
        tests=json.load(l)
    test=tests["ip"]

    for i in test:
        if len(results_ring)>=101:
            break
        counter=-1*float(i)
        #print (counter, i_sum)
        i_sum_ring+=counter
        results_ring.append(counter)
    test=tests["dht"]

    for i in test:
        if len(dht_list_ring)>=101:
            break
        counter=-1*float(i)
        d_sum_ring+=counter
        dht_list_ring.append(counter)

dht=list()
packets_sent=list()
host=list()
host_ring=list()
dht_ring=list()
dht_list.sort()
results.sort()
dht_list_ring.sort()
results_ring.sort()


for i in dht_list:
    dht.append(i/d_sum)
for i in results:
    host.append(i/i_sum)
for i in dht_list_ring:
    dht_ring.append(i/d_sum_ring)
for i in results_ring:
    host_ring.append(i/i_sum_ring)
host=np.cumsum(host)
dht=np.cumsum(dht)
dht_ring=np.cumsum(dht_ring)
host_ring=np.cumsum(host_ring)


#print("test again", dht[-1], host[-1])
#print (dht_list[-1], results[-1], "test")
host.sort()
dht.sort()
#print (dht_list)
#print (d_sum)
#print (i_sum)
#print (len(results), len(dht_list))
p=0
hosts=0

#print (hosts/800)


fig, ax = plt.subplots()
#plt.rc('text', usetex=True)
# Using set_dashes() to modify dashing of an existing line
line1= ax.scatter(x=results,y= host, c="black", s=15,  alpha=.6, label="Classic Packets in Tree", marker="^")
 # 2pt line, 2pt break, 10pt line, 2pt break

# Using plot(..., dashes=...) to set the dashing when creating a line
line2= ax.scatter(x=dht_list, y=dht, s=15, alpha=.6, label="P4CHORD Packets in Tree",  marker="^", c="b")

line3=ax.scatter(x=dht_list_ring, y=dht_ring, s=30, alpha=.2, label="P4CHORD Packets in Ring",  marker="o", c="b")

line4= ax.scatter(x=results_ring,y= host_ring, c="black", s=30,  alpha=.2, label="Classic Packets in Ring", marker="o")
ax.plot(results, host, c="black", alpha=.9,linewidth=1)
ax.plot(results_ring, host_ring, c="black", alpha=.9,linewidth=1)
 # 2pt line, 2pt break, 10pt line, 2pt break

# Using plot(..., dashes=...) to set the dashing when creating a line
ax.plot(dht_list, dht, c="b", alpha=.9, linewidth=1)
ax.plot(dht_list_ring, dht_ring, c="b", alpha=.9, linewidth=1)




ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Probability of Time being Less than or Equal")
ax.legend()
plt.savefig("time_v_packets_cdf.pdf")
plt.show()
