import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add
from pylab import plot, show, savefig, xlim, figure, ylim, legend, boxplot, setp, axes
import statistics



logs= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))

#ring_logs=(glob.glob("../compare_classic_v_dataplane/test_logs/ring_time_1000/*.json"))


classic=list()
one_hop=list()
dht_list=list()
#results_ring=list()
#dht_list_ring=list()
for log in logs:
    with open(log, "r") as l:
        tests=json.load(l)
    print (tests)
    test=tests["ip_classic"]

    for i in test:
        counter=i.split("*")[0]
        counter=float(counter)
        classic.append(counter)
    test=tests["dht"]


    for i in test:

        counter=float(i.split(",")[0])
        dht_list.append(counter)
    test=tests["ip_onehop"]
    for i in test:
        one_hop.append(float(i.split("*")[0]))
fig, ax = plt.subplots()
def setBoxColors(bp):
    setp(bp['boxes'][0], color='blue')
    setp(bp['caps'][0], color='blue')
    setp(bp['caps'][1], color='blue')
    setp(bp['whiskers'][0], color='blue')
    setp(bp['whiskers'][1], color='blue')
    #setp(bp['fliers'][0], markeredgecolor='blue', marker=".")
    #setp(bp['fliers'][1], markeredgecolor='k', marker=".")
    setp(bp['medians'][0], color='red')




    setp(bp['boxes'][1], color='black')
    setp(bp['caps'][2], color='black')
    setp(bp['caps'][3], color='black')
    setp(bp['whiskers'][2], color='black')
    setp(bp['whiskers'][3], color='black')
    setp(bp['medians'][1], color='red')

# Some fake data to plot




# first boxplot pair
#bp = boxplot(A, positions = [1, 3], widths = 0.9, showfliers=False, notch=True)
x= statistics.median(dht_list)
x_c=statistics.median(classic)
x_o= statistics.median(one_hop)
tree_s=str(x_c/x) [0:4]+"x"

"""
r=statistics.median(dht_list_ring)
r_c=statistics.median(results_ring)
ring_s=str(r_c/r)[0:4]+"x"

r_std=np.std(dht_list_ring)
r_c_std=np.std(results_ring)
"""
x_std=np.std(dht_list)
x_c_std=np.std(classic)
x_o_std=np.std(one_hop)
p4=[x]#, r]
classic=[x_c]#, r_c]
one_hop=[x_o]

p4std=[x_std]#, r_std]
classicstd=[ x_c_std]#, r_c_std,]
one_hopstd=[x_o_std]
#print (A_error, A)

p4bar=ax.bar(x=(1), height=p4, yerr=p4std, align='center', alpha=0.8, ecolor='black', capsize=10, color="blue")
classicbar=ax.bar(x=(5),height=classic, yerr=classicstd, align='center', alpha=0.8, ecolor='black', capsize=10, color="grey")
one_hopbar=ax.bar(x=(3),height=one_hop, yerr=one_hopstd, align='center', alpha=0.8, ecolor='red', capsize=10, color="black")

# set axes limits and labels
xlim(0,6)
ylim(0,1)
#ax.set_xticklabels(['Tree Topology', 'Ring Topology'])
#ax.set_xticks([2, 7])
ax.set_ylabel("Time (Seconds)")
# draw temporary red and blue lines and use them to create a legend
hB, = plot([1,1],'b-')
hR, = plot([1,1],'k-')

legend((p4bar, classicbar, one_hopbar),("P4CHORD", 'Classic Chord', "One Hop"))
hB.set_visible(False)
hR.set_visible(False)




plt.savefig("time_bar.pdf")
plt.show()
