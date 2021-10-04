from scapy.all import sendp, send, srp1, sniff
from scapy.all import Packet, hexdump
from scapy.all import Ether, BitEnumField, BitField, IP, ICMP
from scapy.all import bind_layers
import os
import json
import time
import socket
import sys
import threading

max_id=32

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
class Join:
    """
    Queued when a new Join is found
    """
    def __init__(self, ID):
        self.ID = ID
    def return_id():
        return multiprocessing.current_process().ID

class Fail:
    """
    Queued  when host should end
    """
    def __init__(self, on):
       self.on = on
    def on():
       return multiprocessing.current_process().on
class Ack:
    """
    Queued  when host should end
    """
    def __init__(self,time):
       self.time = time
    def on():
       return multiprocessing.current_process().time
class Join_interupt(No_hop_interrupt):
    """
    Raised when  recieved
    """
    pass
class Stabilize_interupt(No_hop_interrupt):
    """
    Raised when ack recieved
    """
    pass

class Message(No_hop_interrupt):
    """
    Raised when message recieved
    """
    def __init__(self,payload, ID):
       self.payload = payload
       self.ID=ID
    pass


class No_hop_host:
    """
    No hop client for sending recieving and running stabilize proccesses
    """
    def __init__(self, client= False, verbose=True, keep_log_files=True, stabilze_timeout=10, ID=None, test=None):
        self.client=client
        self.ID=ID
        self.verbose=verbose
        self.Recieved={"No_hop":list()}
        self.On=True
        self.waiting=0
        self.last_stabilize=time.time()
        self.stabilze_timeout=stabilze_timeout
        self.test=test
        self.keep_log_files=keep_log_files

    def run(self):
        """
        Run corresponding systems for No-hop host
        """
        print ("Starting No-hop")
        if self.client:
            self.send()
        elif (not self.test ==None):
            self.test()
        else:
            thread=  threading.Thread(target = self.start)
            thread.start()
            self.stabilize()
            thread.join()
            self.handle_fail()
            return


    def stabilize(self):
        """
        Stabilize proccess periodically checks succesor
        """
        try:
            while self.On:
                if self.ID==None:
                    continue
                now=time.time()
                if ((now-self.last_stabilize)>=self.stabilze_timeout):
                    self.last_stabilize=now
                    if self.waiting==1:
                        print "Send fail: " + str((self.ID+1)%max_id)
                        send_No_hop(ID=(self.ID+1)%max_id, message="S" ,message_type=2) #Failed node
                        self.waiting=0
                    else:
                        print "Send stabilize: " +str((self.ID+1)%max_id)
                        send_No_hop(ID=(self.ID+1)%max_id, message="S" ,message_type=1)
                        self.waiting=1
        except KeyboardInterrupt:
            self.On=0
            send_No_hop(ID=(self.ID)%max_id, message="Fail" ,message_type=1)
        print("Ending stabilize.")
        return
    def test():
        """
        Send test many ids of every id to test system. Each test message has a payload the time of sending.
        """
        for i in range(self.test):
            for test_id in range(0, max_id):
                test_message= "Sent: "+str(time.time())
                send_No_hop( ID=test_id , message=test_message ,message_type=1, gid=1)
        return

    def send(self):
        """
        Waits for user input to send to another host or client
        """
        print ("No hop Client")
        try:
            while (self.On):
                sys.stdout.flush()
                input = raw_input("Send packet: Type, ID, Message")
                to_send=input.split(",")
                if (not len(to_send)==3):
                    print ("not in correct form. Type, ID, Message")
                else:
                    #print (to_send)
                    send_No_hop(ip="10.0.1.1", ID=int(to_send[1]), message=to_send[2] ,message_type=to_send[0])
                    if self.verbose:
                        print ("sent packet with details id:", to_send[1], " type:", to_send[0], "message:", to_send[2])
        except KeyboardInterrupt:
            print ("Ending No_hop.")
            if not self.client:
                self.recieve_process.join()
                self.stabilize_process.join()
        return
    def handle_join(self, ID):
        """
        Sets ID to the ID that was inclosed in the Join message
        """
        self.ID=ID
        if self.verbose:
            print("Recieved Join with ID=", ID)
        return

    def handle_fail(self):
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
            if (self.ID==None and self.client==False):
                print("No ID or client status, cannot make log files.")
            if not self.ID==None:
                f= open("./packet_log_host_"+str(self.ID)+".txt", "w+")
            else:
                f= open("./packet_log_host_client.txt", "w+")
            print (self.Recieved)
            json.dump(self.Recieved,  f, sort_keys=True, indent=4)
            f.close()
        return

    def handle_message(self, message):
        """
        Handling of type LOOK_UP message, either normal message, ack or stabilize
        """
        print("Recieved message: "+str(message.payload))
        now=time.time()
        mes=message.payload
        ID=int(message.ID)

        self.Recieved["No_hop"].append({"time": now, "ID":ID, "message":mes})
        if "s" in mes:
            send_No_hop(ID=ID, message="ack" ,message_type=1)
        if "ack" in mes:
            self.last_stabilize=now
        if "join" in mes:
            mes=mes.split(":")
            if type(int(mes[1]))==int:
                self.ID=(int(mes[1]))
        return

    def start(self):
        """
        recieves and handles incoming packets for joining, failing , and stabilize
        """
        iface = 'eth0'

        while self.On==1:
            try:
                sniff(iface=iface, prn=handle_packet)
            except KeyboardInterrupt:
                print ("sending shutdown.")
                self.handle_fail()
                self.On=0
                return
            except Message as interrupt:
                self.handle_message(interrupt)

def handle_packet(pkt):
    """
    Recieves and calls apropirate interuptions for No-hop packets
    Is called from sniff.
    """
    sys.stdout.flush()
    if not IP in pkt:
        return
    ttl=str(pkt[IP].ttl)
    if ICMP in pkt:
        return
    #print (pkt)
    if IP in pkt:
        if pkt[IP].proto==2 and pkt[IP].ttl<50:
            raise Message(pkt[No_hop].payload, pkt[No_hop].ID)
    return

def send_No_hop(ip="10.0.1.1", ID=0, message="DHT message for testing" ,message_type=1, gid=1):
    """
    Send a No_hop packet
    """
    ip=ip.split("/")[0]
    addr = socket.gethostbyname(ip)
    pkt = (Ether(dst='00:04:00:00:00:00', type=0x800) / IP(dst=addr, ttl=50, proto=2) / No_hop(message_type=int(message_type), ID=int(ID), gid=gid, counter=0) / message)
    sendp(pkt, iface="eth0")
    return

if __name__ == "__main__":
    if len(sys.argv)<2:
        host= No_hop_host(client=False)
    else:
        if sys.argv[1]=="c":
            host= No_hop_host(client=True)
        elif  type(int(sys.argv[1]))==int:
            host= No_hop_host(client=False, ID=int(sys.argv[1]))
        else:
            raise Exception("Unvalid parameters:", str(sys.argv))
    host.run()
