#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
from ryu.lib import hub
import json
import time
from collections import defaultdict, deque

class IoT_SDN_Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(IoT_SDN_Controller, self).__init__(*args, **kwargs)
        
        # Network monitoring data structures
        self.flow_stats = defaultdict(dict)
        self.mac_to_port = defaultdict(dict)
        self.critical_nodes = set(range(1, 51))
        
        # Start monitoring thread
        self.monitor_thread = hub.spawn(self._monitor_network)
        
    def _monitor_network(self):
        """Background thread to monitor network statistics"""
        while True:
            hub.sleep(10)
            self.logger.info("Network monitoring active - Flows: %d", 
                           sum(len(flows) for flows in self.flow_stats.values()))
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info("Switch %s connected", datapath.id)
    
    def add_flow(self, datapath, priority, match, actions):
        """Add flow entry to switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                              match=match, instructions=inst)
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle packet-in events"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth:
            # Learn port for MAC address
            self.mac_to_port[datapath.id][eth.src] = msg.match['in_port']
            
            if eth.dst in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][eth.dst]
            else:
                out_port = ofproto.OFPP_FLOOD
            
            actions = [parser.OFPActionOutput(out_port)]
            
            # Install flow if not flooded
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(in_port=msg.match['in_port'],
                                      eth_dst=eth.dst)
                self.add_flow(datapath, 1, match, actions)
            
            # Send packet out
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=msg.match['in_port'], actions=actions,
                                    data=msg.data)
            datapath.send_msg(out)

if __name__ == '__main__':
    from ryu.cmd import manager
    manager.main()