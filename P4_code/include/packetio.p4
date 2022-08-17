#ifndef __PACKETIO__
#define __PACKETIO__

#include "headers.p4"
#define CPU_PORT 510
control packetio_ingress(inout headers hdr,
                         inout standard_metadata_t standard_metadata) {
    apply {
        if (standard_metadata.ingress_port == CPU_OUT_PORT) {
            standard_metadata.egress_spec = (bit<9>)hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
            exit;
        }
    }
}

control packetio_egress(inout headers hdr,
                        inout standard_metadata_t standard_metadata) {
    apply {
        if (standard_metadata.egress_port == CPU_OUT_PORT) {
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = (bit<16>)standard_metadata.ingress_port;
        }
    }
}

#endif
