import math
import random
import re
import Data_Plane_DHT_settings

"""
Ring  ID size must match ring size defined in p4 code
"""
""" Please not that if ID space is larger than 100 than the ips for switches must be assigned indiviullay
and cannot use IDs or the hosts... somehow, ip givien sytem must change. (this is only relevant if IPv4 is also implemented on controllers/data plane)"""

hosts=0
class Ring:
    def __init__(self, name,level=0,RING_ID_SIZE=Data_Plane_DHT_settings.RING_SIZE, ip_base="10.0.0.", mac_base=1):
        """
        Name is an IDentifier for the ring
        level is the distance from non DHT Traffic,
        (the farther from leaf nodes the lower the level
        , so the tree grows down)
        """
        if (not type(RING_ID_SIZE)==int):
            raise ValueError ("Ring ID size must be int")
        if (not type(level)==int):
            raise ValueError ("level must be int")


        self.name=name
        self.switches=[]
        self.level=level
        self.ring_ID_size=RING_ID_SIZE
        self.ID_space=1<< RING_ID_SIZE
        self.hosts=[]
        self.ip_base=ip_base
        self.mac_base="08:00:00:00:0"+str(mac_base)+":"

    def free_host_ID(self):
        ID=len(self.hosts)
        while ID in (j.ID for j in self.hosts):
            ID=ID-1

        return ID



    def add_switch(self, switch, max_port_out=30, max_port_in=30, switch_to_controller_port=1, ID=False, classic=True):
        """
        should in normal cases only be run with a string for a name,
        switches should only be created insIDe a Ring object
        """
        if(len(self.switches)>=(self.ID_space-2)):
            """ID_SPACE is the uninclusive max value of valID IDs.
            Where 0 is reserved.
            """
            raise ValueError ("Cannot add switches, Ring is at full capacity")
            return


        if (type(switch)==Switch):
            self.switches.append(switch)
        elif (type(switch)==str):
            self.switches.append(Switch(switch, self , max_port_out, max_port_in, switch_to_controller_port, ID=ID, classic=classic))
        else:
            raise ValueError ("Non valID Switch parameter, either object of class switch or string which will be the name of the switch")

        self.switches.sort(key=lambda x: x.ID,  reverse=False)
        return

    def add_host(self, connected_switches=1, switches=[], client=False):
        """
        connected switches is the amount of switches connected to host,
        switches are which switches, a list of their IDs
        """
        if (connected_switches==0 or connected_switches > len(self.switches)):
            raise ValueError ("must connect to atleast one switch in ring and not more than present")
        spots=list()
        for i in switches:
            if i not in (j.ID for j in self.switches):
                raise ValueError("ID given to connect host to is not an ID of any switch")
            for J in range(len(self.switches)):
                j=self.switches[J]
                if j.ID==i:
                    spots.append(J)

        connect_tmp1=[]
        connect_tmp2=[]
        host_ID=self.free_host_ID()
        if (len(str(host_ID))==1):
            new_host= host("h_"+self.name+str(host_ID), ip=(self.ip_base+str(host_ID)+"/24"), mac=self.mac_base+"0"+str(host_ID), client=client)
        else:
            new_host= host("h_"+self.name+str(host_ID), ip=(self.ip_base+str(host_ID)+"/24"), mac=self.mac_base+str(host_ID), client=client)
        default_command="route add default gw "+ new_host.ip.split("/")[0]+ "0 "+ " dev eth0"

        new_host.commands.append(default_command)
        arp_command= "arp -i eth0 -s "+new_host.ip.split("/")[0]+ "0 "+ new_host.mac[:-2]+"00"
        new_host.commands.append(arp_command)

        self.hosts.append(new_host)
        for i in range(connected_switches):
            if len(switches)>i:
                spot=spots[i]
            else:
                spot=(len(self.hosts)+i) % len(self.switches)
            self.switches[spot].hosts.append(new_host)
            if (not Data_Plane_DHT_settings.bidirectional_connections==1):
                tmp1, tmp2 =make_bIDirectional_connection(switch_a=new_host, switch_b=self.switches[spot], host=new_host)
                connect_tmp2.append(tmp2)
            else:
                tmp1=make_bIDirectional_connection(switch_a=new_host, switch_b=self.switches[spot], host=new_host)

            connect_tmp1.append(tmp1)



        if (not Data_Plane_DHT_settings.bidirectional_connections==1):
            return connect_tmp1, connect_tmp2
        else:
            return connect_tmp1
    def print_switches(self):
        if (Data_Plane_DHT_settings.verbose==0):
            return
        print "Ring "+str(self.name)+":"
        for i in self.switches:
            i.switch_status()
            print "With connections out:"
            for j in i.connections_out:
                j.print_connection(1)
            print "With connections in:"
            for j in i.connections_in:
                j.print_connection(-1)



class host:
    def __init__(self, name, ip, mac, max_port_out=20, max_port_in=20 , ID="ending_num", client=False):
        self.name=name
        if (ID=="ending_num"):
            find=re.match(".*?([0-9]+)$", self.name).group(1)
            if not find:
                print "Either ID mus be given or name end in integer series ID"
                raise ValueError
            else:
                self.ID=find


        self.port_amount_in=max_port_in
        self.port_amount_out=max_port_out
        if client:
            self.ring="client"
            self.name=self.name+"_c"
        else:
            self.ring="host"
        self.switch_to_controller_port=-1

        self.connections_in=[]
        self.connections_out=[]
        global hosts
        hosts+=1
        if hosts>=10:
             self.mac="08:00:00:00:"+str(hosts)+":"+str(hosts)
             self.ip="10.0."+str(hosts)+"."+str(hosts)+"/24"
        else:
            self.mac="08:00:00:00:0"+str(hosts)+":"+str(hosts)*2
            self.ip="10.0."+str(hosts)+"."+str(hosts)+"/24"
        self.commands=[]



class Switch:
    """
    In most cases one should never manually call switch init methods,
    should be done by calling add_switch insIDe a ring object
    """

    def __init__(self, name, ring, max_port_out, max_port_in, switch_to_controller_port, ID=False, classic=True):

        """ For this example we used a pseudo random number gernarator
        Use a hash function that is fitting to your usability requirments
        """


        if type(ID)==int and ring.ID_space-1>= ID and 0<ID:

            tmp_ID=ID
            if tmp_ID in (i.ID for i in ring.switches):

                raise ValueError("explicit ID given for switch in ring "+ str(ring.name)+ " and ID " +str(ID) + " is already taken.")
        else:
            tmp_ID= random.randrange(1,(ring.ID_space-1))
            while (tmp_ID  in (i.ID for i in ring.switches)):
                tmp_ID=random.randrange(1,(ring.ID_space-1))
        self.name=name+"_"+str(ring.name)+"_"+str(tmp_ID)
        self.ID=tmp_ID
        self.alive=0
        self.ring=ring
        self.ports_in_used=[]
        self.classic=classic

        self.hosts=[]


        self.port_amount_in=max_port_in
        self.port_amount_out=max_port_out

        self.switch_to_controller_port=switch_to_controller_port

        """
        connections are a tuple of (port, switch), port being an int
        and switch being the object of the swith connected to
        """
        self.connections_out=[]
        self.connections_in=[]
        if len(str(self.ID))==1:
            self.mac=ring.mac_base+"0"+str(self.ID)
        else:
            self.mac=ring.mac_base+str(self.ID)


        """
        bmv2_connection_object only used if useing bmv2 switches
        """
        self.bmv2_connection_object=0
        return

    def switch_status(self):
        """
        Switch status is to be called in a for loop when looking at all switches in a ring,
        """
        if (Data_Plane_DHT_settings.verbose==0):
            return
        state=" is unresponsive"
        if (self.alive==1):
            state=" is live"
        print str(self.ID)+ state
        return


    def make_tables(self, fail=False):
        vertical_in=[]
        vertical_out=[]
        horizontal=[]
        #print "switch with ID "+ str(self.ID),

        if not fail==False:
            if self==fail[0]:
                fail=fail[1]
            elif self==fail[1]:
                fail=fail[0]
            else:
                fail=False

        before=predesscor(self)
        if self.ring.switches[before]==self:
            print "Only one switch in ring"
            horizontal.append(((0, self.ring.ID_space), ("vertical")))
        else:
            if (not fail==False) and (fail==self.ring.switches[before]):
                    print "Failing link entries for test", fail
            else:
                horizontal.append(((self.ring.switches[before].ID, self.ID), "vertical"))
            i=1
            last_entry=self.ID
            while (len(horizontal)<=self.ring.ring_ID_size):
                #calculate value for entry under chord finger table definition

                entry=(self.ID+ (1<<(i-1))) % (1<<self.ring.ring_ID_size)
                if (Data_Plane_DHT_settings.highly_verbose==1):
                    print str(i) + " entry " +str(entry)
                entry, a_port, connect_s= successor(self, entry)
                if (Data_Plane_DHT_settings.highly_verbose==1):
                    print "succesor "+ str(entry)
                i+=1

                if (not fail==False) and (fail==connect_s):
                    print "Failing link entries for test"
                else:
                    horizontal.append(((last_entry, entry), ("dht_forward", a_port)) )
                last_entry=entry

            if (not fail==False) and (fail==connect_s):
                    print "Failing link entries for test", self.name, connect_s.name
            else:
                horizontal.append(((0, self.ring.ID_space),("dht_forward", a_port)))

        vertical_lookup_in=[]
        vertical_lookup_out=[]


        host_connections=[]
        client_connection=[]



        for i in self.connections_out:

            direction=i.direction

            if (Data_Plane_DHT_settings.bidirectional_connections==1):
                if (not i.switch_a== self):
                    direction= direction * (-1)
            if (i.switch_a==self):
                switch_b=i.switch_b
                a_port=i.a_port
                switch_a=i.switch_a
            else:
                switch_b=i.switch_a
                a_port=i.b_port
                switch_a=i.switch_b
            if (not fail==False) and (fail==switch_b):
                print "Failing link entries for test", self.name, switch_b.name
                continue

            if(switch_b.ring=="host"):
                host_connections.append(a_port)
                continue

            if (switch_b.ring=="client"):
                client_connection.append(a_port)
                continue


            elif direction==1:
                 # incoming
                host_connections.append(a_port)


            elif direction==-1:
                 # response
                client_connection.append(a_port)


            elif (not i.switch_a.ring==i.switch_b.ring) and direction==2 or direction==-2:
                if len(switch_a.hosts)==0:
                    host_connections.append(a_port)
        if (len(host_connections)>0):
            print "vertical ports for "+ str(self.name)
            for i in host_connections:
                print i
            for i in range(self.ring.ID_space+1):
                connection=i%(len(host_connections))
                vertical_lookup_in.append((i,host_connections[connection]))
        if (len(client_connection)>0):
            for i in range(self.ring.ID_space+1):
                connection=i%(len(client_connection))
                vertical_lookup_out.append((i,client_connection[connection]))


        #vertical_lookup_out.sort(key =lambda x: x[0])
        #vertical_lookup_in.sort(key= lambda x: x[0])

        """ This section is for the controller, it adds values in the range() and for that value
        value_0 must be less than value_1"""

        tmp_horzontal=[]

        for i in horizontal:
            #print i, i[0]
            if (i[0][0] > i[0][1]):
                range_1, range_2= change_order(i[0], self)
                #print i[0], range_1, range_2
                tmp_horzontal.append((range_1, i[1]))
                tmp_horzontal.append((range_2, i[1]))
            elif (i[0][0]==i[0][1]):
                tmp_horzontal.append(((i[0][0],(i[0][0])+1), i[1]))
            else:
                tmp_horzontal.append(i)

        horizontal=tmp_horzontal


        return horizontal, vertical_lookup_in, vertical_lookup_out

def change_order(key_range, switch):

    range_1=(key_range[0],switch.ring.ID_space)
    range_2=(0,key_range[1])

    return range_1, range_2

def predesscor(switch):
    spot=switch.ring.switches.index(switch)

    if (len(switch.ring.switches)==1):
        return 0
    if (spot==0):
        before=len(switch.ring.switches)-1
    else:
        before=spot-1
    return before



def successor(switch, ID, direction=0):

    successor=switch
    port=-1

    cap=switch.ring.ID_space
    for i in switch.connections_out:
        if (i.switch_a==switch):
            switch_b=i.switch_b
            a_port=i.a_port
        else:
            switch_b=i.switch_a
            a_port=i.b_port
        if i.direction==direction:
            """
            horizontal
            """
            tmp_cap=distance(ID, switch_b)
            if (Data_Plane_DHT_settings.highly_verbose==1):
                print "distance between "+str(ID)+ " and " + str(switch_b.ID)+ " = "+str(tmp_cap)
            if (tmp_cap and tmp_cap<cap):
                cap=tmp_cap
                successor=switch_b.ID
                port=a_port
                switch=switch_b


    return successor, port , switch


def distance(ID, switch):
    node_ID=switch.ID
    if (node_ID<ID):
        return ((switch.ring.ID_space-ID)+node_ID)
    if (node_ID>ID):
        return (node_ID-ID)
    if (node_ID==ID):
        return 0

def active_ports(switch):
    active_ports=[]
    for i in switch.connections_out:
        if i.switch_a==switch:
            active_ports.append(i.a_port)
        if i.switch_b==switch:
            active_ports.append(i.b_port)
    for i in switch.connections_in:
        if i.switch_a==switch:
            active_ports.append(i.a_port)
        if i.switch_b==switch:
            active_ports.append(i.b_port)
    return active_ports


class connection:
    """
    If no ports are given in with parameters a_pot and b_port one will be assigned
    """
    def __init__(self, switch_a,switch_b, a_port=-1, b_port=-1, host="none"):
        """
        connection from switch_a to switch_b
        """

        if ((len(switch_a.connections_out))>=switch_a.port_amount_out-1):
            raise ValueError ("Not enough outgoing ports from  " + str(switch_a.name)+ " available for a new connection.")
        if (len(switch_b.connections_in)>=switch_b.port_amount_in):
            raise ValueError ("Not enough ports into Switch " + str(switch_b.name)+ " available for a new connection.")
        if (a_port in (i.a_port for i in switch_b.connections_out)):
            raise ValueError ("Port given for outgoing port for switch: "+ str(switch_a.name) + "is already in use." )
        if (b_port in (i.b_port for i in switch_b.connections_in)):
            raise ValueError ("Port given for incoming port for switch: "+ str(switch_b.name) + "is already in use." )
        if (a_port not in range(-1,switch_a.port_amount_out)):
            raise ValueError ("Port given for a_port is not a valID port for switch: "+ str(switch_a.name))
        if (b_port not in range(-1,switch_b.port_amount_in)):
            raise ValueError ("Port given for a_port is not a valID port for switch: "+ str(switch_b.name))
        if ((a_port==switch_a.switch_to_controller_port) and not switch_a==host):
            raise ValueError ("port given for a_port is the designated port to controller for  switch "+ str(switch_a.name))
        if ((b_port==switch_b.switch_to_controller_port) and not switch_b==host):
            raise ValueError ("port given for a_port is the designated port to controller for  switch "+ str(switch_b.name))
        if (switch_a==switch_b):
            raise ValueError("switch_a and switch_b are the same switch. Connection was not made.")



        if (host=="none"):
            direction=switch_b.ring.level-switch_a.ring.level
            if (switch_b.ring==switch_a.ring):
                """horizontal connection"""
                self.direction=0 # 0 is for horizontal
            elif (direction==0):
                self.direction=2
                """if len(switch_b.hosts)>0:
                    self.direction=1
                elif len(switch_a.hosts)>0:
                    self.direction=-1"""

                if (Data_Plane_DHT_settings.verbose==0):
                    print "Rings on same logical level, connection will only be passed to switch if other connections fail"
            if (direction>0):
                """
                down, a is closer to root than b
                """
                self.direction=1
            if (direction<0):
                """
                up a is closer to leaf than b
                """
                self.direction=-1
        if (host==switch_a):
            self.direction=-1
        if (host==switch_b):
            self.direction=1
        """
        Port Assigment
        """

        if (Data_Plane_DHT_settings.bidirectional_connections==1):
            a_port=(switch_a.switch_to_controller_port+1) % (switch_a.port_amount_out)
            while (a_port in active_ports(switch_a)):
                a_port=(a_port+1) % (switch_a.port_amount_out)
                if a_port==switch_a.switch_to_controller_port:
                    a_port=(a_port+1) % switch_a.port_amount_out


            b_port=(switch_b.switch_to_controller_port+1)% (switch_b.port_amount_in)
            while (b_port in active_ports(switch_b)):
                b_port=(b_port+1) % (switch_b.port_amount_in)
                if b_port==switch_b.switch_to_controller_port:
                    b_port=(b_port+1) % (switch_b.port_amount_in)
        else:
            a_port=(switch_a.switch_to_controller_port+1) % (switch_a.port_amount_out)
            while (a_port in (i.a_port for i in switch_a.connections_out)):
                a_port=(a_port+1) % (switch_a.port_amount_out)
                if a_port==switch_a.switch_to_controller_port:
                    a_port=(a_port+1) % switch_a.port_amount_out

            b_port=(switch_b.switch_to_controller_port+1)% (switch_b.port_amount_in)
            while (b_port in (i.b_port for i in switch_b.connections_in)):
                b_port=(b_port+1) % (switch_b.port_amount_in)
                if b_port==switch_b.switch_to_controller_port:
                    b_port=(b_port+1) % (switch_b.port_amount_in)


        self.a_port=a_port
        self.b_port=b_port
        self.switch_a=switch_a
        self.switch_b= switch_b

        switch_a.connections_out.append(self)
        if (Data_Plane_DHT_settings.bidirectional_connections==1):
            switch_b.connections_out.append(self)
        else:
            switch_b.connections_in.append(self)
        self.live=0

    def remove(self):
        self.switch_a.connections_out.remove(self)
        self.switch_b.connections_in.remove(self)
        del self
        return

    def print_connection(self, inout):
        if (Data_Plane_DHT_settings.verbose==0):
            return
        if (inout==1):
            arrow="------>"
            print "(Switch "+ str(self.switch_a.ID)+") in (Ring " +str(self.switch_a.ring.name)+ ") (Port: "+ str(self.a_port)+ ") "+arrow+" Switch (" + str(self.switch_b.ID) + ") in (Ring "+str(self.switch_b.ring.name) + ") (Port: "+ str(self.b_port)+")"
        elif(inout==-1):
            arrow="<------"
            print "(Switch "+ str(self.switch_b.ID)+") in (Ring " +str(self.switch_b.ring.name)+ ") (Port: "+ str(self.b_port)+ ") "+arrow+" Switch (" + str(self.switch_a.ID) + ") in (Ring "+str(self.switch_a.ring.name) + ") (Port: "+ str(self.a_port)+")"



def make_string_from_connection(c, host="none"):
    if "h" in c.switch_a.name:
        host=c.switch_a
    if "h" in c.switch_b.name:
        host=c.switch_b
    if host=="none":
        str1=str(c.switch_a.name)+"-p"+str(c.a_port)
        str2=str(c.switch_b.name)+"-p"+str(c.b_port)
    if host==c.switch_a:
        str1=str(c.switch_a.name)
        str2=str(c.switch_b.name)+"-p"+str(c.b_port)
    if host==c.switch_b:
        str1=str(c.switch_a.name)+"-p"+str(c.a_port)
        str2=str(c.switch_b.name)
    return (str1, str2)

def make_bIDirectional_connection(switch_a, switch_b, host="none"):

    c_1= connection(switch_a, switch_b, host=host)

    if (not Data_Plane_DHT_settings.bidirectional_connections==1):
        c_2 = connection(switch_b, switch_a, host=host)
        return c_1, c_2
    return c_1
