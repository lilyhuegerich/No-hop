import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add
from pylab import plot, show, savefig, xlim, figure, ylim, legend, boxplot, setp, axes, bar
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

    #print (bp["boxes"])
    #setp(bp['boxes'][1], color='black')
    setp(bp['caps'][2], color='black')
    setp(bp['caps'][3], color='black')
    setp(bp['whiskers'][2], color='black')
    setp(bp['whiskers'][3], color='black')
    setp(bp['medians'][1], color='red')

# Some fake data to plot

A=[dht_list]#, results]
B=[one_hop]#, results_ring]
C=[classic]


# first boxplot pair
bp1 = boxplot(A, positions = [5], widths = 0.9, showfliers=False, notch=True)
x= statistics.median(dht_list)
x_c=statistics.median(classic)
x_o=statistics.median(one_hop)
tree_s=str(x_c/x) [0:4]+"x"


# second boxplot pair
bp2 = boxplot(B, positions = [3], widths = 0.9, showfliers=False, notch=True)
bp3 = boxplot(C, positions = [1], widths = 0.9, showfliers=False, notch=True)

bp4 = boxplot([0], positions = [7], widths = 0.9, showfliers=False, notch=True)

setp(bp1['boxes'][0], color='blue')
setp(bp1['caps'][0], color='blue')
setp(bp1['caps'][1], color='blue')
setp(bp1['whiskers'][0], color='blue')
setp(bp1['whiskers'][1], color='blue')
setp(bp1['medians'][0], color='blue')

#print (bp["boxes"])"""""
"""setp(bp3['boxes'][0], color='c')
setp(bp3['caps'][0], color='c')
setp(bp3['caps'][1], color='c')
setp(bp3['whiskers'][0], color='c')
setp(bp3['whiskers'][1], color='c')"""
setp(bp2['medians'][0], color='black')

setp(bp3['medians'][0], color='black')
#setBoxColors(bp)
plt.annotate("", xy=( 5,x ), xytext=(7.6, x ),
             arrowprops=dict(arrowstyle="-", color="black", alpha=.3), )
plt.annotate("", xy=( 3,x_o ), xytext=(7.6, x_o ),
             arrowprops=dict(arrowstyle="-", color="black", alpha=.3), )

plt.annotate("", xy=( 1,x_c ), xytext=(7.6, x_c ),
             arrowprops=dict(arrowstyle="-", color="black", alpha=.3), )

plt.annotate("", xy=( 6.4,x ), xytext=(7.6, x ),
             arrowprops=dict(arrowstyle="-", color="blue", alpha=1), )
plt.annotate("", xy=( 6.4,x_o ), xytext=(7.6, x_o ),
             arrowprops=dict(arrowstyle="-", color="black", alpha=1), )

plt.annotate("", xy=( 6.4,x_c ), xytext=(7.6, x_c ),
             arrowprops=dict(arrowstyle="-", color="black", alpha=1), )


plt.annotate("", xy=( 8,x-.005 ), xytext=(8, x_o+.005 ),
             arrowprops=dict(arrowstyle="|-|", color="black", alpha=.3), )

plt.annotate("", xy=( 8.7 ,x-.005), xytext=(8.7, x_c+.005 ),
             arrowprops=dict(arrowstyle="|-|", color="black", alpha=.3), )

plt.annotate(str(x_c/x)[0:4]+"x",  xy=(8.3, x_c+.005 ))
plt.annotate(str(x_o/x)[0:4]+"x",  xy=(7.6, x_o+.005))


#plt.annotate("", xy=( 1.5,x ), xytext=(2.3, x ),
             #connectionstyle='-', color="black" )

#plt.annotate("", xy=( 1.5, x_o), xytext=(4.5, x_c ), arrowprops=dict(arrowstyle="<|-|>", color="green"), )

#plt.text(1.5, .06, tree_s, color= 'green', fontsize=12)
#plt.text(6.4, .085, ring_s, color= 'green', fontsize=12)


# thrid boxplot pair

# set axes limits and labels
xlim(0,9.5)
ylim(0,.6)
ax.set_xticklabels(['No-hop','1-hop' , 'Chord', "Mediums"])
ax.set_xticks([1,  3, 5, 7])
ax.set_ylabel("Time (Seconds)")
# draw temporary red and blue lines and use them to create a legend
hB, = plot([1,1],'b-')
hR, = plot([1,1],'k-')
hl,=plot([1,1], 'c-')
#hl=plot([1,1], "purple-")

#egend((hB, hR, hl),("P4CHORD", "One Hop", 'Classic Chord'))
hB.set_visible(False)
hR.set_visible(False)
hl.set_visible(False)




plt.savefig("time_v_packets_box.pdf")
plt.show()
