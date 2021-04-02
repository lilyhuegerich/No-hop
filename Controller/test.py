import Data_Plane_DHT
import random
import make_topology


def main ():
    """ Sloppy make_topology and Data plane Dht tests"""

    AMOUNT_OF_RINGS=3
    AMOUNT_OF_SWITCHES=20
    rings=[]
    for i in range(AMOUNT_OF_RINGS):
        rings.append(Data_Plane_DHT.Ring(str(i),level=i))
        for j in range(AMOUNT_OF_SWITCHES):
            rings[i].add_switch(str(j))
    """
    for i in range(1):
        for j in range(5):
            if (j<4):
                Data_Plane_DHT.connection(rings[i].switches[j], rings[i].switches[j+1])
        Data_Plane_DHT.connection(rings[i].switches[4], rings[i].switches[0])
    """
    """
    for i in range(1):
        for j in range(5):
            if (j<3):
                Data_Plane_DHT.connection(rings[i].switches[j], rings[i].switches[j+2])
        Data_Plane_DHT.connection(rings[i].switches[4], rings[i].switches[1])
        Data_Plane_DHT.connection(rings[i].switches[3], rings[i].switches[0])
        """

    for i in range(10):
        tmp_1=random.randrange(0,AMOUNT_OF_SWITCHES)
        tmp_2=random.randrange(0,AMOUNT_OF_SWITCHES)
        S_1=random.randrange(0,AMOUNT_OF_RINGS)
        S_2=random.randrange(0,AMOUNT_OF_RINGS)
        while (S_1==S_2 and tmp_1==tmp_2):
            S_1=random.randrange(0,AMOUNT_OF_RINGS)
            S_2=random.randrange(0,AMOUNT_OF_RINGS)
            tmp_1=random.randrange(0,AMOUNT_OF_SWITCHES)
            tmp_2=random.randrange(0,AMOUNT_OF_SWITCHES)
        try:
            Data_Plane_DHT.connection(rings[S_1].switches[tmp_1], rings[S_2].switches[tmp_2])
        except ValueError:
            break


    """"
    for i in range(1,AMOUNT_OF_SWITCHES):
        try:
            Data_Plane_DHT.connection(rings[0].switches[0], rings[0].switches[i])
        except ValueError:
            break
    """
    """
    for i in range(1,AMOUNT_OF_SWITCHES):
        try:
            Data_Plane_DHT.make_bidirectional_connection(rings[0].switches[0], rings[1].switches[i])
        except ValueError:
            break
        rings[0].print_switches()



    finger, vertical_in, vertical_out= rings[0].switches[0].make_tables()
    print vertical_in
    """
    print "check"
    #make_topology.quick_test()
    make_topology.tree_topo()

if  __name__ == '__main__':
    main()
