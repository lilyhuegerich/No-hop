#include <core.p4>
#include <v1model.p4>
#include "include/headers.p4"
#include "include/packetio.p4"

const bit<16> TYPE_DHT = 0x1212;
const bit<16> TYPE_IPV4 = 0x800;





/***** Below 6 lines taken from P4v16 language specification *****/
/* special output port values for outgoing packet */

typedef bit<9> PortId;
const PortId DROP_PORT = 0xF;
const PortId RECIRCULATE_OUT_PORT = 0xD;
/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                           H E A D E R                             -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */



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
        transition select(standard_metadata.ingress_port){
            CPU_OUT_PORT: parse_packet_out;
            default: parse_ethernet;
        }
    }

    state parse_packet_out {
        packet.extract(hdr.packet_out);
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

    counter(32, CounterType.packets) fail;
    counter(32, CounterType.packets) join;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(bit<48>  dstAddr, bit<9> port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        standard_metadata.egress_spec = port;
    }

    action no_hop_forward(bit<9> port){
        standard_metadata.egress_spec = port;

    }

    action send_to_controller(){
          standard_metadata.egress_spec = CPU_OUT_PORT;
          hdr.packet_in.setValid();
          hdr.packet_in.ingress_port = (bit<16>)standard_metadata.ingress_port;
      }
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
            no_hop_forward;                      /* switch rewrites packet headers */
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
            send_to_controller();
            }
	    }
        else{
            ipv4_lpm.apply();
        }
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
        packet.emit(hdr.packet_in);
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
