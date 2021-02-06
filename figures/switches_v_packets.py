import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add
logs= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))
log_rings= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))

results=list()
dht_list=list()
results_o=list()
d=0
i_t=0
o=0


for log in logs:
    with open(log, "r") as l:
        tests=json.load(l)
    test=tests["ip_classic"]
    for i in test:
        i=float(i.split("*")[1])
        i_t+=i
        results.append(i)
    test=tests["dht"]
    for i in test:
        i=i.split(",")[1]

        d+=int(i)
        dht_list.append(int(i))
    test=tests["ip_onehop"]
    for i in test:
        i=i.split("*")[1]
        o+=float(i)
        results_o.append(float(i))

dht=list()
dht_ring=list()
host_list=list()
host_o=list()
packets_sent=list()
host_ring=list()
p=0
hosts=0

dht_list.sort()
results_o.sort()
results.sort()
o=float(o)
i_t=float(i_t)
d=float(d)


for i in dht_list:
    i=float(i)
    dht.append(i/d)
for i in results:
    i=float(i)
    host_list.append(i/i_t)
for i in results_o:
    i=float(i)
    host_o.append(i/o)


host_list=np.cumsum(host_list)
host_o=np.cumsum(host_o)
dht= np.cumsum(dht)

fig, ax = plt.subplots()
plt.xticks(np.arange(0,25 , 1.0))
#plt.rc('text', usetex=True)
# Using set_dashes() to modify dashing of an existing line

line1= ax.scatter(x=results,y= host_list, c="c", s=15,  alpha=.05, marker="o")

line2= ax.scatter(x=dht_list, y=dht, s=15, alpha=.05,  marker="o", c="black")

line3=ax.scatter(x=results_o, y=host_o, s=15, alpha=.05,  marker="o", c="b")

"""
#below is so all lines continue till end
results_ring.append(23)
host_ring=np.append(host_ring, 1)

dht_list_ring.append(23)
dht_ring=np.append(dht_ring,1)

results.append(23)
host_list=np.append(host_list,1)

dht_list.append(23)
dht=np.append(dht, 1)
"""

line4, =ax.plot(dht_list,dht, linewidth=1, alpha=1, c="b",label="P4CHORD")

line6, =ax.plot(results_o, host_o, linewidth=1.5, alpha=1, c="black",   linestyle="dotted", label="One Hop")

line5, = ax.plot(results,  host_list, c="c", linewidth=1.5,  alpha=1,  linestyle= "dotted", label="Chord")








#line1 = ax.plot(packets_sent, host,"k", dashes=[6, 2], label='Classic')
 # 2pt line, 2pt break, 10pt line, 2pt break

# Using plot(..., dashes=...) to set the dashing when creating a line
#line2, = ax.plot(packets_sent, dht, "b",  label='Data Plane')


"""plt.annotate("", xy=(130, dht[129]), xytext=(130, host[129] ),
             arrowprops=dict(arrowstyle="<->", color="gray"), )
""""""
#plt.text(105, 500, r'$\Delta m \approx$'+str(slope_dif),
         {'color': 'gray', 'fontsize': 18, 'ha': 'center', 'va': 'center',
          'bbox': dict(boxstyle="round", fc="white", ec="gray", pad=0.2)})
plt.text(105, 280, r'$m\approx$'+slope_dht,
         {'color': 'blue', 'fontsize': 18, 'ha': 'center', 'va': 'center'})

#plt.text(105, 950, r'$m\approx$'+slope_ip,
        # {'color': 'black', 'fontsize': 18, 'ha': 'center', 'va': 'center'})
"""
ax.set_xlabel("Switch Traversals")
ax.set_ylabel("CDF")
ax.legend()
plt.savefig("switch_contacts_versus_packets.pdf")
plt.show()
