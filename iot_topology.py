#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time
import subprocess

class IoTTopology:
    def __init__(self, num_nodes=400):
        self.num_nodes = num_nodes
        self.net = None
        
    def create_topology(self):
        """Create hierarchical IoT topology"""
        info('*** Creating IoT topology with %s nodes\n', self.num_nodes)
        
        # Create network with remote controller
        self.net = Mininet(controller=RemoteController, switch=OVSSwitch, link=TCLink)
        
        info('*** Adding controller\n')
        c0 = self.net.addController('c0', controller=RemoteController, 
                                  ip='127.0.0.1', port=6653)
        
        # Create hierarchical topology
        self._create_hierarchical_topology()
        
        info('*** Starting network\n')
        self.net.start()
        
        info('*** Testing network connectivity\n')
        self.net.pingAll()
        
        info('*** Running CLI\n')
        CLI(self.net)
        
        info('*** Stopping network\n')
        self.net.stop()
    
    def _create_hierarchical_topology(self):
        """Create a hierarchical topology"""
        # Core switches
        core_switches = []
        for i in range(2):
            sw = self.net.addSwitch('cs%d' % (i+1))
            core_switches.append(sw)
        
        # Aggregation switches
        agg_switches = []
        for i in range(10):
            sw = self.net.addSwitch('as%d' % (i+1))
            agg_switches.append(sw)
            
            # Connect to core
            for core_sw in core_switches:
                self.net.addLink(sw, core_sw, bw=1000)
        
        # Edge switches
        edge_switches = []
        for i in range(40):
            sw = self.net.addSwitch('es%d' % (i+1))
            edge_switches.append(sw)
            
            # Connect to aggregation
            agg_index1 = i % 10
            agg_index2 = (i + 5) % 10
            self.net.addLink(sw, agg_switches[agg_index1], bw=100)
            self.net.addLink(sw, agg_switches[agg_index2], bw=100)
        
        # IoT devices
        host_id = 1
        for i, edge_sw in enumerate(edge_switches):
            for j in range(10):
                if host_id > self.num_nodes:
                    break
                    
                host = self.net.addHost('h%d' % host_id)
                self.net.addLink(host, edge_sw, bw=10)
                host_id += 1

if __name__ == '__main__':
    setLogLevel('info')
    topology = IoTTopology(num_nodes=400)
    topology.create_topology()