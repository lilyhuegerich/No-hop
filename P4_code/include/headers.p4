#ifndef __HEADERS__
#define __HEADERS__

// packet in
@controller_header("packet_in")
header packet_in_header_t {
    bit<16>  ingress_port;
}

// packet out
@controller_header("packet_out")
header packet_out_header_t {
    bit<16> egress_port;
    bit<16> mcast_grp;
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
    packet_out_header_t     packet_out;
    packet_in_header_t      packet_in;
    ethernet_t ethernet;
    ipv4_t ipv4;
    dht_t dht;
}

 struct metadata {

}

#endif
