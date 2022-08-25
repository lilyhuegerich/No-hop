/*
Copyright 2021 Intel Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include <core.p4>
#include <v1model.p4>


header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

#define CPU_PORT 510
header dht_t {
    bit<2>  message_type;       /* message type */
    bit<6> id;                           /* packet id*/
    bit<6> group_id;               /*tentative implementation of group defined DHT subdivision */
    bit<10>  counter;              /* please note that counter is not an actual field just for testing */
}
const bit<6> first_valid_id= 0;
const bit<6> last_valid_id=32;


typedef bit<16> PortIdToController_t;

enum bit<8> ControllerOpcode_t {
    NO_OP                    = 0,
    SEND_TO_PORT_IN_OPERAND0 = 1
}

enum bit<8> PuntReason_t {
    IP_OPTIONS          = 1,
    UNRECOGNIZED_OPCODE = 2,
    DEST_ADDRESS_FOR_US = 3
}

@controller_header("packet_out")
header packet_out_header_t {
    ControllerOpcode_t   opcode;
    bit<8>  reserved1;
    bit<32> operand0;
    bit<32> operand1;
    bit<32> operand2;
    bit<32> operand3;
}

@controller_header("packet_in")
header packet_in_header_t {
    PortIdToController_t input_port;
    PuntReason_t         punt_reason;
    ControllerOpcode_t   opcode;
    bit<32> operand0;
    bit<32> operand1;
    bit<32> operand2;
    bit<32> operand3;
}

struct metadata_t {
}

struct headers_t {
    packet_in_header_t  packet_in;
    packet_out_header_t packet_out;
    ethernet_t ethernet;
    ipv4_t     ipv4;
    dht_t dht;
}

parser parserImpl(packet_in packet,
                  out headers_t hdr,
                  inout metadata_t meta,
                  inout standard_metadata_t stdmeta)
{
    const bit<16> ETHERTYPE_IPV4 = 16w0x0800;

    state start {
        transition check_for_cpu_port;
    }
    state check_for_cpu_port {
        transition select (stdmeta.ingress_port) {
            CPU_PORT: parse_controller_packet_out_header;
            default: parse_ethernet;
        }
    }
    state parse_controller_packet_out_header {
        packet.extract(hdr.packet_out);
        transition accept;
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            ETHERTYPE_IPV4: parse_ipv4;
            default: parse_dht;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition parse_dht;
    }
    state parse_dht {
        packet.extract(hdr.dht);
        transition accept;
    }
}

control ingressImpl(inout headers_t hdr,
                    inout metadata_t meta,
                    inout standard_metadata_t stdmeta)
{
    action send_to_controller_simple(PuntReason_t punt_reason) {
        stdmeta.egress_spec = CPU_PORT;
        hdr.packet_in.setValid();
        hdr.packet_in.input_port = (PortIdToController_t) stdmeta.ingress_port;
        hdr.packet_in.punt_reason = punt_reason;
        hdr.packet_in.opcode = ControllerOpcode_t.NO_OP;
        hdr.packet_in.operand0 = 1;
        hdr.packet_in.operand1 = 2;
        hdr.packet_in.operand2 = 3;
        hdr.packet_in.operand3 = 4;
    }
    action send_to_controller_with_details(
        PuntReason_t       punt_reason,
        ControllerOpcode_t opcode,
        bit<32> operand0,
        bit<32> operand1,
        bit<32> operand2,
        bit<32> operand3)
    {
        stdmeta.egress_spec = CPU_PORT;
        hdr.packet_in.setValid();
        hdr.packet_in.input_port = (PortIdToController_t) stdmeta.ingress_port;
        hdr.packet_in.punt_reason = punt_reason;
        hdr.packet_in.opcode = opcode;
        hdr.packet_in.operand0 = operand0;
        hdr.packet_in.operand1 = operand1;
        hdr.packet_in.operand2 = operand2;
        hdr.packet_in.operand3 = operand3;
    }
    action my_drop() {
        mark_to_drop(stdmeta);
    }
    action set_port(bit<9> port) {
        stdmeta.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl |-| 1;
    }
    action punt_to_controller() {
        send_to_controller_simple(PuntReason_t.DEST_ADDRESS_FOR_US);
    }
    table ipv4_da_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            set_port;
            punt_to_controller;
            my_drop;
        }
        default_action = my_drop;
    }

    table dbgPacketOutHdr {
        key = {
            hdr.packet_out.opcode : exact;
            hdr.packet_out.reserved1 : exact;
            hdr.packet_out.operand0 : exact;
            hdr.packet_out.operand1 : exact;
            hdr.packet_out.operand2 : exact;
            hdr.packet_out.operand3 : exact;
        }
        actions = { NoAction; }
        const default_action = NoAction;
    }
    counter(32, CounterType.packets) fail;
    counter(32, CounterType.packets) join;

    action first_contact(){

       hash (hdr.dht.id,
               HashAlgorithm.crc32,
               first_valid_id,
               { hdr.ethernet.dstAddr,
                hdr.ethernet.srcAddr,
                  hdr.ethernet.etherType},
                last_valid_id);
       hdr.dht.message_type=1;
    }

    table no_hop_lookup {
        key={
            hdr.dht.group_id           : exact;
            hdr.dht.id               : range;      /* can be replaced with ternary but controller has to be changed for switches without range match type */
        }
        actions={
            set_port;                      /* switch rewrites packet headers */
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }

    apply {


    if (hdr.ipv4.isValid()){
          hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
      }
      if (hdr.dht.isValid()){
          if (hdr.dht.message_type==0){
              first_contact();
          }
      if (hdr.dht.message_type==1){
          no_hop_lookup.apply();
      }
      if (hdr.dht.message_type==3 || hdr.dht.message_type==2){
           if (hdr.dht.message_type==2){
               fail.count((bit<32>)  hdr.dht.id);
           }
           if (hdr.dht.message_type==3){
               join.count((bit<32>)  hdr.dht.id);
           }
              send_to_controller_simple(PuntReason_t.IP_OPTIONS);

          }
    }
      else{

          //ipv4_lpm.apply();
          send_to_controller_simple(PuntReason_t.IP_OPTIONS);

          }send_to_controller_simple(PuntReason_t.IP_OPTIONS);
    }
}

control egressImpl(inout headers_t hdr,
                   inout metadata_t meta,
                   inout standard_metadata_t stdmeta)
{
    apply {
    }
}

control deparserImpl(packet_out packet,
                     in headers_t hdr)
{
    apply {
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.dht);
    }
}

control verifyChecksum(inout headers_t hdr, inout metadata_t meta) {
    apply {
        verify_checksum(hdr.ipv4.isValid() && hdr.ipv4.ihl == 5,
            { hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum, HashAlgorithm.csum16);
    }
}

control updateChecksum(inout headers_t hdr, inout metadata_t meta) {
    apply {
        update_checksum(hdr.ipv4.isValid() && hdr.ipv4.ihl == 5,
            { hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum, HashAlgorithm.csum16);
    }
}

V1Switch(parserImpl(),
         verifyChecksum(),
         ingressImpl(),
         egressImpl(),
         updateChecksum(),
         deparserImpl()) main;
