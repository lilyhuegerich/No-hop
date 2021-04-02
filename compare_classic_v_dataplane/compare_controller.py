#!/usr/bin/env python2
import argparse
import grpc
import os
import sys
from time import sleep
import random



sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../Controller/'))


import Data_Plane_DHT
import Data_Plane_DHT_settings
import make_topology

import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper


def write_ip_lpm_rules(p4info_helper, switch):

    lpm_table=make_topology.generate_ipv4_lpm_table(switch)
    print "generating lpm table for switch "+str(switch.name)

    for i in lpm_table:
        print i
        table_entry = p4info_helper.buildTableEntry(
        table_name="ThisIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": (i[0], i[1])
        },
        action_name="ThisIngress.ipv4_forward",
        action_params={"dstAddr": i[3],
                        "port": i[2]})
        switch.bmv2_connection_object.WriteTableEntry(table_entry)

    print "Entered IPv4 LPM rules for switch "+ str(switch.name)

def write_finger_table_Rule(p4info_helper, switch, finger_table):
    keys=[]
    for i in finger_table:

        print "adding table rules for switch " + str(switch.name) + "with keys " + str(i)
        for j in range(i[0][0], i[0][1]):
            if j in keys:
                continue
            if len(keys)>=8:
                continue
            print j
            keys.append(j)
            if (i[1]=="vertical"):
                table_entry = p4info_helper.buildTableEntry(
                    table_name="ThisIngress.finger_table_lookup",
                    match_fields={
                        "hdr.dht.id": j},
                    action_name="ThisIngress.vertical_lookup"
                        )
            else:
                table_entry = p4info_helper.buildTableEntry(
                    table_name="ThisIngress.finger_table_lookup",
                    match_fields={
                        "hdr.dht.id": j
                        },
                    action_name="ThisIngress.dht_forward",
                    action_params={"port": i[1][1]}
                    )
            #print (i)
            #print(table_entry)
            switch.WriteTableEntry(table_entry)
    return

def write_vertical_lookup_Rule(p4info_helper, switch, vertical_in, vertical_out):
    keys_i=[]
    print "adding vertical table rules for switch " + str(switch.name) + " with keys "
    for i in vertical_in:

        for j in range(0,i[0]):
            if j in keys_i:
                continue
            keys_i.append(j)
            print j
            table_entry = p4info_helper.buildTableEntry(
                table_name="ThisIngress.vertical_lookup_in_table",
                match_fields={
                    "hdr.dht.id": j
                    },
                action_name="ThisIngress.dht_forward",
                action_params={
                    "port": i[1]
                    })
            switch.WriteTableEntry(table_entry)
    keys_o=[]
    for i in vertical_out:
        for j in range(0, i[0]):
            if j in keys_o:
                continue
            keys_o.append(j)
            table_entry = p4info_helper.buildTableEntry(
                table_name="ThisIngress.vertical_lookup_out_table",
                match_fields={
                    "hdr.dht.id": j
                    },
                action_name="ThisIngress.dht_forward",
                action_params={
                    "port": i[1]
                    })
            switch.WriteTableEntry(table_entry)

def stabilize(address, id):
    return id

def prepare_ring(ring, p4info_helper, bmv2_file_path, ring_ip_base=0):
    #print "preparing switches in ring "+ ring.name
    dif=0

    for i in ring.switches:

            i.bmv2_connection_object=(p4runtime_lib.bmv2.Bmv2SwitchConnection(
                name=i.name,
                address='127.0.0.1:'+ str(50050+ring_ip_base+dif),
                device_id=dif+ring_ip_base-1,
                proto_dump_file='../P4/logs/'+ i.name+'-p4runtime-requests.txt'))
                # Send master arbitration update message to establish this controller as
            i.bmv2_connection_object.MasterArbitrationUpdate()

            dif+=1

            # Install the P4 program on the switches
            i.bmv2_connection_object.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                           bmv2_json_file_path=bmv2_file_path)

            horizontal, vertical_lookup_in, vertical_lookup_out= i.make_tables()


            #write_finger_table_Rule(p4info_helper=p4info_helper, switch=i.bmv2_connection_object, finger_table=horizontal)

            #write_vertical_lookup_Rule(p4info_helper=p4info_helper, switch=i.bmv2_connection_object, vertical_in=vertical_lookup_in, vertical_out=vertical_lookup_out)

            write_ip_lpm_rules(p4info_helper=p4info_helper, switch=i)
    return

""""
Function print grpc errors taken from p4 tutorials
"""
def printGrpcError(e):
    print "gRPC Error:", e.details(),
    status_code = e.code()
    print "(%s)" % status_code.name,
    traceback = sys.exc_info()[2]
    print "[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)

def readTableRules(p4info_helper, sw):
    """
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print '\n----- Reading tables rules for %s -----' % sw.name
    for response in sw.ReadTableEntries():


        for entity in response.entities:
            entry = entity.table_entry

            table_name = p4info_helper.get_tables_name(entry.table_id)
            print '%s: ' % table_name,
            for m in entry.match:
                print p4info_helper.get_match_field_name(table_name, m.field_id),
                print '%r' % (p4info_helper.get_match_field_value(m),),
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print '->', action_name,
            for p in action.params:
                print p4info_helper.get_action_param_name(action_name, p.param_id),
                print '%r' % p.value,
            print


def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)


    try:


        if Data_Plane_DHT_settings.test==1:
            ring=make_topology.test_ring()
            prepare_ring(ring=ring,ring_ip_base=1, p4info_helper=p4info_helper, bmv2_file_path=bmv2_file_path)
            for i in ring.switches:
                readTableRules(p4info_helper, i.bmv2_connection_object)
        else:

            ring_v0_1, ring_v1_1, ring_v1_2= make_topology.basic_3_ring()
            prepare_ring(ring=ring_v0_1, ring_ip_base=1, p4info_helper=p4info_helper, bmv2_file_path=bmv2_file_path)
            prepare_ring(ring=ring_v1_1, ring_ip_base=5, p4info_helper=p4info_helper, bmv2_file_path=bmv2_file_path)
            prepare_ring(ring=ring_v1_2, ring_ip_base=9, p4info_helper=p4info_helper, bmv2_file_path=bmv2_file_path)

            for i in ring_v0_1.switches:
                readTableRules(p4info_helper, i.bmv2_connection_object)
            for i in ring_v1_1.switches:
                readTableRules(p4info_helper, i.bmv2_connection_object)

            for i in ring_v1_2.switches:
                readTableRules(p4info_helper, i.bmv2_connection_object)

        while True:

            sleep(2)


    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/compare_dht.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/compare_dht.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
        parser.exit(1)
    main(args.p4info, args.bmv2_json)
