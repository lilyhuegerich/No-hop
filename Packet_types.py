from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP

max_id=32

class No_hop(Packet):
    name = "No_hop"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"LOOK_UP", 2:"FAILURE", 3:"JOIN" }),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="gid", default=1, size=6),
                        BitField(name="counter", default=0, size=10)
                       ]

class Source_int(Packet):
	name="Source_int"
	fields_desc = [BitEnumField(name="bottom_of_stack", default=0, size=1, enum={0:"mid_stack",1:"bottom_of_stack"}),
                        BitEnumField(name="to_metric", default=0, size=1, enum={0:"No_int", 1:"int"}),
                        BitField(name="port", default=0, size=14)
                       ]


