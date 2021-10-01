from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import bind_layers
import os
import json
import time
import socket
import sys

class No_hop(Packet):
    name = "No_hop"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"LOOK_UP", 2:"FAILURE", 3:"JOIN" }),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="gid", default=1, size=6),
                        BitField(name="counter", default=0, size=10)]

bind_layers(IP, No_hop, proto=2)
bind_layers(Ether, IP, type=0x800)
