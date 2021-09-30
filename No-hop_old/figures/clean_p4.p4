
#define RING_ID_SIZE 6
#define CPU_OUT_PORT 0
#define ID_SPACE 1<<RING_ID_SIZE

const bit<16> TYPE_DHT = 0x1212;

typedef bit<RING_ID_SIZE> node_id;

const node_id first_valid_id=1;
const node_id last_valid_id=ID_SPACE-1;

/* -:-:-:                           H E A D E R                             -:-:-:*/

header ethernet_t {
    bit<48>      dstAddr;
    bit<48>      srcAddr;
    bit<16>      etherType;
   }

header dht_t {
    bit<2>  message_type;       /* message type */
    node_id id;                         /* packet id*/
}

struct headers {
    ethernet_t ethernet;
    dht_t dht;
}

 struct metadata {

}

/*-:-:-:                           P A R S E R                          -:-:-:*/

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
            TYPE_DHT: parse_dht;
            default: accept;
        }
    }

    state parse_dht {
        packet.extract(hdr.dht);
        transition accept;
    }
}

/* -:-:-:                         I N G R E S S                        -:-:-:*/

control ThisIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action dht_forward(bit<9> port){
        standard_metadata.egress_spec=port;
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
            hdr.dht.id               : exact;
        }
        actions={
            dht_forward;                      /* switch passes on to switch at same logical level */
            vertical_lookup;              /* vertical lookup brings lookup closer to leaf, meeing this is the switch responsible for the request */
            send_to_controller;
            NoAction;
        }
        size = 70;
        default_action = NoAction();
    }

    apply {
        if (hdr.dht.isValid()){
            if (hdr.dht.message_type==0){
                first_contact();
            }
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
    }
}

/* -:-:-:                           E G R E S S                          -:-:-: */

control ThisEgress(inout headers hdr,
                inout metadata meta,
                    inout standard_metadata_t standard_metadata) {
	apply {		}
}

  /* -:-:-:                         D E P A R S E R                        -:-:-:*/

control ThisDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.dht);
    }
}
