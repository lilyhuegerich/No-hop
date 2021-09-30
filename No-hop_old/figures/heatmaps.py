import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import glob
import json
from operator import add
logs= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))
log_rings= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))


def split_up(data):
    row=0
    r= np.zeros((10, 100))
    while row<10:
        x=0
        while x<100:
            r[row][x]=data[row*100+x]
            x=x+1
        row=row+1
    return r




def load_data():

    logs= (glob.glob("../compare_classic_v_dataplane/test_logs/*.json"))
    hop0=list()
    hop1=list()
    chord=list()
    hosts=list()
    for log in logs:


        with open(log, "r") as l:
            tests=json.load(l)
        test=tests["ip_classic"]
        for i in test:
            i=float(i.split("*")[1])

            chord.append(int(i))
        test=tests["dht"]
        for i in test:
            i=i.split(",")[1]


            hop0.append(int(i))
        test=tests["ip_onehop"]
        for i in test:
            i=i.split("*")[1]

            hop1.append(float(i))
        hosts.append((chord, hop1, hop0))
    max= np.max(chord)
    print (max)
    print (chord, hop1, hop0)
    fig, ax = plt.subplots(3)
    hop1=split_up(hop1)
    print (hop1)
    chord=split_up(chord)
    hop0=split_up(hop0)

    ax[0].set_title("Chord")
    im=ax[0].imshow(chord, vmin=3, vmax=22, cmap="binary")
    ax[0].set_xticks([])
    ax[0].set_yticks([])

    ax[1].set_title("1-Hop")
    ax[1].imshow(hop1, vmin=3, vmax=22, cmap="binary")
    ax[1].set_xticks([])
    ax[1].set_yticks([])

    ax[2].set_title("No-Hop")
    im=ax[2].imshow(hop0, vmin=3, vmax=22, cmap="binary")
    ax[2].set_xticks([])
    ax[2].set_yticks([])

    fig.colorbar(im, ax=ax[2], orientation='horizontal',  fraction=.1)


    plt.savefig("nheatmap.pdf")
    plt.show()

    return hosts
load_data()
