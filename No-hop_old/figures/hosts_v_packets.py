import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add
logs= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))


results=list()

for log in logs:
    with open(log, "r") as l:
        test=json.load(l)
    test=test["ip"]
    for i in test:
        print (i)
        i=i.split(",")
        counter=1
        for j in i:
            #print (j)
            if ("h_R" in j):
                counter+=1
        results.append(counter)
print (len(results))
dht=list()
packets_sent=list()
host=list()
i=0
hosts=0
for i in range(800):
    dht.append(i)
    packets_sent.append(i)
    host.append(hosts)
    hosts=hosts+results[i]
    i+=1
print (hosts/800)





fig, ax = plt.subplots()
#plt.rc('text', usetex=True)
# Using set_dashes() to modify dashing of an existing line
line1, = ax.plot(packets_sent, host,"k", label='Classic')
 # 2pt line, 2pt break, 10pt line, 2pt break

# Using plot(..., dashes=...) to set the dashing when creating a line
line2, = ax.plot(packets_sent, dht, "k", dashes=[6, 2], label='Data Plane')


plt.annotate("", xy=( 800, 800), xytext=(800, host[799] ),
             arrowprops=dict(arrowstyle="<->", color="gray"), )

plt.text(650, 1350, r'$\Delta m \approx1.965$',
         {'color': 'gray', 'fontsize': 18, 'ha': 'center', 'va': 'center',
          'bbox': dict(boxstyle="round", fc="white", ec="gray", pad=0.2)})
plt.text(650, 2300, r'$m\approx2.965$',
         {'color': 'black', 'fontsize': 18, 'ha': 'center', 'va': 'center'})

plt.text(650, 800, r'$m=1$',
         {'color': 'black', 'fontsize': 18, 'ha': 'center', 'va': 'center'})

ax.set_xlabel("Packets Sent")
ax.set_ylabel("Total End Host Contacts")
ax.legend()
plt.savefig("end_host_contacts_versus_packets.pdf")
plt.show()
