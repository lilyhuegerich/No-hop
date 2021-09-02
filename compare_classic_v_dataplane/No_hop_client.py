from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import bind_layers
import os
import json
import time
from multiprocessing import Process

class No_hop(Packet):
    name = "No_hop"
    fields_desc = [BitEnumField(name="message_type", default=2, size=2, enum={0:"FIRST_CONTACT",1:"LOOK_UP", 2:"FAILURE", 3:"JOIN" }),
                        BitField(name="ID", default=0, size=6),
                        BitField(name="gid", default=1, size=6),
                        BitField(name="counter", default=0, size=10)]

bind_layers(IP, No_hop, proto=2)
bind_layers(Ether, IP, type=0x800)

class No_hop_interrupt(Exception):
    """
    Base class for no hop interrupts
    """
    pass
class Join(No_hop_interrupt):
    """
    Raised when a new Join is found
    """
    pass
class Fail(No_hop_interrupt):
    """
    Raised when host should end
    """
    pass
class Message(No_hop_interrupt):
    """
    Raised when message recieved
    """
    pass

class No_hop_client:
    """
    No hop client for sending recieving and running stabilize proccesses
    """
    def __init__(self, client= False, verbose=True, keep_log_files=True, stabilze_timeout=100):
        self.client=client
        self.ID=None
        self.verbose=verbose
        self.Recieved={"No_hop":list()}
        self.last_stabilize= None
        self.stabilze_timeout=stabilze_timeout
        self.waiting=0
        self.On=True

        self.recieve_process= Process(target= self.start()) # Starts to listen for packets
        self.send_proccess=Proccess(target= self.send()) # Prepares to send user input
        self.stabilize_process=Proccess(target= self.stabilize()) # Begins stabilization proccess

    def stabilize(self):
        """
        Stabilize proccess periodically checks succesor
        """
        while self.On:
            if self.ID==None:
                continue
            now=time.time()
            if ((now-self.last_stabilize)<self.stabilze_timeout):
                if self.waiting==1:
                    send_No_hop(ID=self.ID+1, message="S" ,message_type=2):
                else:
                    send_No_hop(ID=self.ID+1, message="S" ,message_type=1):
                    self.waiting=1
        return
    def send(self):
        """
        Waits for user input to send to another host or client
        """
        while (self.On):
            input = raw_input("Send packet: Type, ID, Message")
            sys.stdout.flush()
            to_send=input.split(",")
            if (not len(to_send)==3:
                print ("not in correct form. Type, ID, Message")
            else:
                send_No_hop(ip="10.0.1.1", ID=int(to_send[1]), message=to_send[2] ,message_type=to_send[0])
                if self.verbose:
                    print ("sent packet with details id:", to_send[1], " type:", to_send[0], "message:", to_send[2])
        return
    def handle_join(self, ID):
        """
        Sets ID to the ID that was inclosed in the Join message
        """
        self.ID=ID
        if self.verbose:
            print("Recieved Join with ID=", ID)
        return

    def handle_fail(self, message):
        """
        Response to a known failure, writes logs and sends shutdown message
        """
        if self.verbose:
            print("Recieved Fail message, shutting down")
        self.write_logs()
        self.On=False
        return

    def write_logs(self):
        """
        if keep_log_files=True: writes recieved packets to log file
        """
        if self.keep_log_files:
            if self.ID=None and self.client==False:
                print("No ID or client status, cannot make log files.")
            if not self.ID==None:
                f= open("./packet_log_host_"+str(self.ID)+".txt", "w+")
            else:
                f= open("./packet_log_host_client.txt", "w+")
            json.dump(self.Recieved,  f, sort_keys=True, indent=4)
            f.close()
        return

    def handle_message(self, pkt):
        """
        Handling of type LOOK_UP message, either normal message, ack or stabilize
        """
        now=time.time()
        mes=str(pkt[IP].payload)
        ID=pkt[No_hop].ID
        self.Recieved["No_hop"].append({"time": now, "ID", ID, "message", mes})
        if "S" in mes:
            self.waiting=0
            send_No_hop(ID=ID, message="ack" ,message_type=1):
        if "ack" in mes:
            self.last_stabilize=now
        return

    def start(self,):
        """
        recieves and handles incoming packets for joining, failing , and stabilize
        """
        while self.On:
            try:
                sniff(iface=iface, prn=handle_packet)
            except KeyboardInterrupt:
                self.write_logs()
                return
            except Join as interrupt:
                self.handle_join(interrupt)
            except Fail as interrupt:
                self.handle_fail(interrupt)
            except Message as interrupt:
                self.handle_message(interrupt)
        return

def handle_packet(pkt):
    """
    Recieves and calls apropirate interuptions for No-hop packets
    Is called from sniff.
    """
    sys.stdout.flush()
    ttl=str(pkt[IP].ttl)
    if ICMP in pkt:
        return
    if (not ttl=="50"):
        if IP in pkt:
            if pkt[IP].proto==2:
                if pkt[No_hop].message_type==3:
                    raise Join (pkt[No_hop].ID)
                if pkt[No_hop].message_type==2:
                    raise Fail("Fail.")
                if pkt[No_hop].message_type==1:
                    raise Message(pkt)
    return

def send_No_hop(ip="10.0.1.1", ID, message="DHT message for testing" ,message_type=1):
    """
    Send a No_hop packet
    """
    ip=ip.split("/")[0]
    addr = socket.gethostbyname(ip)
    pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / No_hop(message_type=message_type, ID=int(ID), gid=1 , counter=0) / message)
    sendp(pkt, iface="eth0")
    return
