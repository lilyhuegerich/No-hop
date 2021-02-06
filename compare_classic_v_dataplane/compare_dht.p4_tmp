#include <core.p4>
#include <v1model.p4>



#define RING_ID_SIZE 6  /* Please note that ID size changes on ID space, meening this field might have to be changed depending on size of ring */
#define ID_SPACE 1<<RING_ID_SIZE


const bit<16> TYPE_DHT = 0x1212;
const bit<16> TYPE_IPV4 = 0x800;




typedef bit<RING_ID_SIZE> node_id;

/***** Below 6 lines taken from P4v16 language specification *****/
/* special output port values for outgoing packet */

typedef bit<9> PortId;
const PortId DROP_PORT = 0xF;
const PortId CPU_OUT_PORT = 0xE;
const PortId RECIRCULATE_OUT_PORT = 0xD;


const node_id first_valid_id=1;
const node_id last_valid_id=ID_SPACE-1;
/*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
   -:-:-:                           H E A D E R                             -:-:-:
-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */




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
    node_id id;                 /* packet id*/
    bit<8>  counter;            /* please note that counter is not an actual field just for testing */
}

struct headers {
    ethernet_t ethernet;
    dht_t dht;
    ipv4_t ipv4;
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
            default: parse_dht;
        }
    }

    state parse_dht {
        packet.extract(hdr.dht);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
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


    counter(8192, CounterType.packets_and_bytes) ingressDHTCounter;
    counter(8192, CounterType.packets_and_bytes) egressDHTCounter;

    /* drop():
        Packet has been determined as not to be proccesed.
    */

    action drop() {
        mark_to_drop(standard_metadata);
    }

    /* send_to_controller():
        send packet to controller
        Used for tabilize proccess
    */
    action ipv4_forward(bit<48>  dstAddr, bit<9> port) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action dht_forward(bit<9> port){
        standard_metadata.egress_spec=port;
        egressDHTCounter.count((bit<32>) hdr.dht.id);
    }

    action send_to_controller(){
          standard_metadata.egress_spec = CPU_OUT_PORT;
      }


    action vertical_lookup(){
        /* vertical lookup functionality is implemented in vertical lookup in and out tables, this function later triggers these tables, ententionally empty */
    }


    /* first_contact():
        This is incase of the incoming packet not yet haveing an ID.
        The ID is calculated based on a hash of packet values.
        The hash values can be changed to fit implementation
    */
    action first_contact(){

        /* on first contact messages the value of ingoing or outgoing is saved in the id.
        This is only nessacary if the leaf nodes do not calculate the ids themselves*/

        hdr.dht.message_type= hdr.dht.id[1:0];

        /* The ID for the packet is then calculcated
        this is done useing a hash algorithm of choice with data to hash of choice.
        Hash algorithm and inputs can be choosen to fit application requirments

        base and max should stay the same.
        Base=1 since id 0 is reserved
        Max= the largest possible id, or ID_SPACE, to addapt this please change RING_ID_SIZE defintion.
        */

        hash (hdr.dht.id,
                HashAlgorithm.crc32,
                first_valid_id,
                { hdr.ipv4.srcAddr,
	               hdr.ipv4.dstAddr,
                   hdr.ipv4.protocol},
                 last_valid_id);

    }
    table vertical_lookup_in_table{
        key={
            hdr.dht.id            : exact;
        }
        actions={
            dht_forward;
            NoAction;
        }
        size= 70;
        default_action= NoAction();
    }

    table vertical_lookup_out_table{
        key={
            hdr.dht.id            : exact;
        }
        actions={
            dht_forward;
            NoAction;
        }
        size=70;
        default_action= NoAction();
    }

    table finger_table_lookup {
        key={
            hdr.dht.id               : exact;      /* can be replaced with ternary but controller has to be changed for switches without range match type */
        }
        actions={
            dht_forward;                      /* switch passes on to switch at same logical level */
            vertical_lookup;              /* vertical lookup brings lookup closer to leaf, meeing this is the switch responsible for the request */
            send_to_controller;                       /* either this will be intended for succesor (packet id node id +1) or should be sent back to controller if  id= node id */
            NoAction;
        }
        size = 70;
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
        if (hdr.dht.isValid()){
            if (hdr.dht.message_type==0){
                first_contact();
            }
            ingressDHTCounter.count((bit<32>) hdr.dht.id);
            hdr.dht.counter=hdr.dht.counter+1;
            switch   (finger_table_lookup.apply().action_run)   {
		vertical_lookup: {
                if (hdr.dht.message_type==1){
                    send_to_controller();
                }
                if (hdr.dht.message_type==2){
                    vertical_lookup_in_table.apply();
                }
                if (hdr.dht.message_type==3){
                    vertical_lookup_out_table.apply();
                }
		}
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
        packet.emit(hdr.ethernet);
        packet.emit(hdr.dht);
        packet.emit(hdr.ipv4);
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
