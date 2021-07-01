/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_RANDOMFOREST = 0x1234;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header randomforest_t {
    bit<32> id;
    bit<32> age;
    bit<32> sex;
    bit<32> p_class;
    bit<32> fare;
    bit<32> survived;
    bit<32> switch_survived;    
    bit<32> counter;
    bit<32> depth;
}

struct metadata {
    /* empty */
}

struct headers {
    ethernet_t      ethernet;
    randomforest_t  randomforest;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {    
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_RANDOMFOREST: parse_randomforest;
            default: accept;
        }
    }

    state parse_randomforest {
        packet.extract(hdr.randomforest);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {


    action packet_forward() {
        standard_metadata.egress_spec = 2;
        if(((hdr.randomforest.counter == 5) && (hdr.randomforest.switch_survived >= 3)) ||
            ((hdr.randomforest.counter == 4) && (hdr.randomforest.switch_survived >= 2)) ||
            ((hdr.randomforest.counter == 3) && (hdr.randomforest.switch_survived >= 2)) ||
            ((hdr.randomforest.counter == 2) && (hdr.randomforest.switch_survived >= 1)) ||
            ((hdr.randomforest.counter == 1) && (hdr.randomforest.switch_survived == 1)))
        {
            hdr.randomforest.switch_survived = 1;
        }
        else
        {
            hdr.randomforest.switch_survived = 0;
        }
    }

    apply {
        if (hdr.randomforest.isValid()) {
            packet_forward();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply { }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.randomforest);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
