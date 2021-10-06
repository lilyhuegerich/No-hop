#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_DHT = 0x1212;
const bit<16> TYPE_IPV4 = 0x800;



/***** Below 6 lines taken from P4v16 language specification *****/
/* special output port values for outgoing packet */

typedef bit<9> PortId;
const PortId DROP_PORT = 0xF;
#define CPU_OUT_PORT 255
const PortId RECIRCULATE_OUT_PORT = 0xD;

/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                           H E A D E R                             -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */

@controller_header("packet_out")
header packet_out_header_t {
    bit<16> egress_port;
}
@controller_header("packet_in")
header packet_in_header_t {
    bit<16> ingress_port;
}


header ethernet_t {
    bit<48>      dstAddr;
    bit<48>      srcAddr;
    bit<16>      etherType;
   }
 header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    bit<32>   srcAddr;
    bit<32>   dstAddr;
}


header dht_t {
    bit<2>  message_type;       /* message type */
    bit<6> id;                 /* packet id*/
    bit<6> group_id;             /*tentative implimintation of group deinfened DHT subdivision */
    bit<10>  counter;            /* please note that counter is not an actual field just for testing */
}

struct headers {
    ethernet_t ethernet;
    ipv4_t ipv4;
    dht_t dht;
}

 struct metadata {

}


/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                           P A R S E R                          -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */

parser ThisParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: parse_ipv4;
        }
    }

    state parse_dht {
        packet.extract(hdr.dht);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select (hdr.ipv4.protocol){
            2: parse_dht;
            default: accept;
        }

	}
}


/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                 V E R I F Y _ C H E C K S U M                -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */


control ThisChecksum( inout headers hdr, inout metadata meta) {
     apply {  }
}


/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                         I N G R E S S                        -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */


control ThisIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {


    action drop() {
        mark_to_drop(standard_metadata);
    }


    action ipv4_forward(bit<48>  dstAddr, bit<9> port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        standard_metadata.egress_spec = port;
    }

    action dht_rewrite(bit<32> dht_address){
        hdr.ipv4.dstAddr=dht_address;
    }

    action send_to_controller(){
         standard_metadata.egress_spec = CPU_OUT_PORT;
      }

    table no_hop_lookup {
        key={
            hdr.dht.group_id           : exact;
            hdr.dht.id               : range;      /* can be replaced with ternary but controller has to be changed for switches without range match type */
        }
        actions={
            dht_rewrite;                      /* switch rewrites packet headers */
            send_to_controller;                       /* either this will be intended for succesor (packet id node id +1) or should be sent back to controller if  id= node id */
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
    apply {
        bool found=false;
        if (hdr.ipv4.isValid()){
            hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        }
        if (hdr.dht.isValid()){
        if (hdr.dht.message_type==1){
            if (no_hop_lookup.apply().hit){
                found=true;
                }
            }
            if (hdr.dht.message_type==3 || hdr.dht.message_type==2){
                send_to_controller();
                found=true;
            }
	    }

        if found==false
        {
            ipv4_lpm.apply();
        }

}

/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                           E G R E S S                          -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */


control ThisEgress(inout headers hdr,
                inout metadata meta,
                    inout standard_metadata_t standard_metadata) {
	apply {		}
}


/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                 C O M P U T E _ C H E C K S U M                -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */

control ThisChecksumCompute(inout headers  hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
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
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}
/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                         D E P A R S E R                        -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */


control ThisDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.dht);
    }
}

/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                 V 1   M O D E L   S W I T C H                -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */


V1Switch(
ThisParser(),
ThisChecksum(),
ThisIngress(),
ThisEgress(),
ThisChecksumCompute(),
ThisDeparser()
)main;
