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

    bit<32> nodeid = 0;
    bit<1>  nodebool = 0;
    bit<32> nodeval = 0;

    action decision(bit<32> next, bit<32> feat, bit<32> thr, bit<32> depth) {
       if(feat == 0)
       {
            nodeval = hdr.randomforest.age;
       }
       else if(feat == 1)
       {
            nodeval = hdr.randomforest.sex;
       }
       else if(feat == 2)
       {
            nodeval = hdr.randomforest.p_class;
       }        
       else if(feat == 3)
       {
            nodeval = hdr.randomforest.fare;
       }

       if(nodeval >= thr)
       {
            nodebool = 1;
       }
       else
       {
            nodebool = 0;
       }
       nodeid = next;
       if(depth > hdr.randomforest.depth)
       {
            hdr.randomforest.depth = depth;
       }
    }
    
    table depth_0 {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            decision;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table depth_1 {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            decision;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table depth_2 {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            decision;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table depth_3 {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            decision;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table depth_4 {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            decision;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    action packet_forward(egressSpec_t port, bit<32> result) {
        standard_metadata.egress_spec = port;

        hdr.randomforest.switch_survived = hdr.randomforest.switch_survived + result;
    }
    
    table forward {
        key = {
            nodeid: exact;
            nodebool: exact;
        }
        actions = {
            packet_forward;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }
    
    apply {
        if (hdr.randomforest.isValid()) {
        	depth_0.apply();
            depth_1.apply();
            depth_2.apply();
            depth_3.apply();
            depth_4.apply();
            if(nodeid != 0)
            {
                hdr.randomforest.counter = hdr.randomforest.counter + 1;
            }
            forward.apply();
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
