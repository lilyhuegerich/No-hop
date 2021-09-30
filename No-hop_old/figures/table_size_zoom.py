import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
import json
from operator import add
howmany=40
breakp=1000
howmany2=1000000
def rewritetable(hosts, size, ip=False):

     v= (hosts* ((2*size)+ 32))  #hosts many entries of size id size + ipv4 size
     if ip:
         return v+1024
     else:
        return v
def fttable(hosts, size):
    return (size* ((2*size) + 9)) # fingertable with size entries of size, (size +16) plus an 16 bit return port
def rewrite_total(hosts, size, ip=False, switchper=10):
    s=int(hosts/switchper)
    if s*switchper<hosts:
        s=s+1
    return (rewritetable(hosts, size, ip=ip)*s)
def fttotal(hosts, size):
    return (fttable(hosts,size)*hosts)
def ft(hosts, spots):
    i=0
    tables=spots[0]
    while hosts>tables:
        i=i+1
        tables=spots[i]

    return  i

def make_spots(length):
    spots=list()
    for i in range(length):
        spots.append(2**i)
    return spots


spots=make_spots(howmany)
#print (spots)
r=list()
f=list()
ftots=list()
rtots=list()

rip=list()


rtotsip=list()

for i in range (howmany):
    size=ft(i, spots)
    #print (i, ft(i, spots))
    f.append(fttable(i, size))
    r.append(rewritetable(i, size))
    ftots.append(fttotal(i, size))
    rtots.append(rewrite_total(i, size))

    rip.append(rewritetable(i, size, ip=True))
    rtotsip.append(rewrite_total(i, size, ip=True))
x=np.arange(0, howmany, 1)
fig, (ax3, ax4) = plt.subplots(nrows=2, figsize=(4,8))
ax1 =  zoomed_inset_axes(ax3, 10500, loc=2) # zoom = 2
ax2 =  zoomed_inset_axes(ax4, 10500, loc=2) # zoom = 2)
#ax1.set_yscale('log')
#ax2.set_yscale('log')
ax1.plot(x, r, c="gray", label="rewrite")
ax1.plot(x, f, c="b", label="fingertable")
ax1.plot(x, rip, c="k", label="rewrite with IP table", linestyle=":" )
ax2.plot(x, ftots, c="b", label="fingertable total")
ax2.plot(x, rtots, c="gray", label="rewrite total" )
ax2.plot(x, rtotsip, c="k", label="rewrite total with IP table", linestyle=":" )
#ax1.legend()
#ax2.legend()

r=list()
f=list()
ftots=list()
rtots=list()

rip=list()


rtotsip=list()


for i in range (0, howmany2):
    size=ft(i, spots)
    #print (i, ft(i, spots))
    f.append(fttable(i, size))
    r.append(rewritetable(i, size))
    ftots.append(fttotal(i, size))
    rtots.append(rewrite_total(i, size))

    rip.append(rewritetable(i, size, ip=True))
    rtotsip.append(rewrite_total(i, size, ip=True))
x=np.arange(0, howmany2, 1)

#ax3.set_yscale('log')
#ax4.set_yscale('log')
ax3.plot(x, r, c="gray", label="Rewrite" )

ax3.plot(x, rip, c="k", label="Rewrite with IP table", linestyle=":" )
ax3.plot(x, f, c="b", label="Fingertable")
ax3.set_title("Single Switch Table")
ax4.set_title("All Switch Tables")


ax4.plot(x, ftots, c="b", label="fingertable total")
ax4.plot(x, rtots, c="gray", label="rewrite total")
ax4.plot(x, rtotsip, c="k", label="rewrite total with IP table", linestyle=":" )
ax1.set_xlim(0, 40)
ax1.set_ylim(0, 2500)
ax2.set_ylim(0, 150000)
ax2.set_xlim(0, 40)

mark_inset(ax3, ax1, loc1=2, loc2=4, fc="none", ec="0.5")
mark_inset(ax4, ax2, loc1=2, loc2=4, fc="none", ec="0.5")

ax4.legend(bbox_to_anchor=(0., -.75, 1, .102), loc="lower center",
               ncol=3, mode="expand", borderaxespad=0)
#ax4.legend()
fig.text(0.55, 0.175, 'Supported Hosts', va='center', ha='center')
fig.text(0.02, .6, 'Size (Bits)', va='center', ha='center', rotation='vertical')
fig.tight_layout()
plt.savefig("tablesize.pdf")
#plt.draw()
plt.show()
