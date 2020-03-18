#! /usr/bin/env python
# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2018 Intel Corporation

from __future__ import print_function

import socket
import os
import sys
import time
import json
import signal

BUFFER_SIZE = 200000
clients = []

METRICS_REQ = "{\"action\":0,\"command\":\"ports_all_stat_values\",\"data\":null}"
API_REG = "{\"action\":1,\"command\":\"clients\",\"data\":{\"client_path\":\""
API_UNREG = "{\"action\":2,\"command\":\"clients\",\"data\":{\"client_path\":\""
GLOBAL_METRICS_REQ = "{\"action\":0,\"command\":\"global_stat_values\",\"data\":null}"
DEFAULT_FP = "/var/run/dpdk/default_client"

ports_desired_stats = {
    "rx_missed_errors": True,
    "rx_good_packets": True,
    "tx_good_packets": True,
    "rx_good_bytes": True,
    "tx_good_bytes": True,
}

global_desired_stats = {
    "empty_poll": True,
    "full_poll": True,
    "busy_percent": True,
}


try:
    raw_input  # Python 2
except NameError:
    raw_input = input  # Python 3

class Socket:

    def __init__(self):
        self.send_fd = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.recv_fd = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.client_fd = None

    def __del__(self):
        try:
            self.send_fd.close()
            self.recv_fd.close()
            self.client_fd.close()
        except:
            print("Error - Sockets could not be closed")

class Client:

    def __init__(self): # Creates a client instance
        self.socket = Socket()
        self.file_path = None
        self.choice = None
        self.unregistered = 0
        self.prev_stats = {}

    def __del__(self):
        try:
            if self.unregistered == 0:
                self.unregister();
        except:
            print("Error - Client could not be destroyed")

    def getFilepath(self, file_path): # Gets arguments from Command-Line and assigns to instance of client
        self.file_path = file_path

    def getPrefix(self, prefix): # Gets arguments from Command-Line and assigns to instance of client
        self.prefix = prefix

    def register(self): # Connects a client to DPDK-instance
        if os.path.exists(self.file_path):
            os.unlink(self.file_path)
        try:
            self.socket.recv_fd.bind(self.file_path)
        except socket.error as msg:
            print ("Error - Socket binding error: " + str(msg) + "\n")
        self.socket.recv_fd.settimeout(2)
        self.socket.send_fd.connect("/var/run/dpdk/" + self.prefix + "/telemetry")
        JSON = (API_REG + self.file_path + "\"}}")
        self.socket.send_fd.sendall(JSON)
        self.socket.recv_fd.listen(1)
        self.socket.client_fd = self.socket.recv_fd.accept()[0]

    def unregister(self): # Unregister a given client
        self.socket.client_fd.send(API_UNREG + self.file_path + "\"}}")
        self.socket.client_fd.close()
        self.unregistered = 1

    def requestMetrics(self): # Requests metrics for given client
        self.socket.client_fd.send(METRICS_REQ)
        data = self.socket.client_fd.recv(BUFFER_SIZE)
        return data

    def requestGlobalMetrics(self): #Requests global metrics for given client
        self.socket.client_fd.send(GLOBAL_METRICS_REQ)
        data = self.socket.client_fd.recv(BUFFER_SIZE)
        return data
    
    def initMetrics(self):
        ports_data = json.loads(self.requestMetrics())
        for port_data in ports_data["data"]:
            port = port_data["port"]
            for stat in port_data["stats"]:
                if stat["name"] in ports_desired_stats:
                    self.prev_stats[str(stat["name"]) + "-port" + str(port)] = stat["value"]

        global_data = json.loads(self.requestGlobalMetrics())
        for stat in global_data["data"][0]["stats"]:
            if stat["name"] in global_desired_stats:
                self.prev_stats[str(stat["name"])] = stat["value"]

    def getMetrics(self):
        stats = {"timestamp": time.time()}
        ports_data = json.loads(self.requestMetrics())
        for port_data in ports_data["data"]:
            port = port_data["port"]
            for stat in port_data["stats"]:
                if stat["name"] in ports_desired_stats:
                    metric = str(stat["name"]) + "-port" + str(port)
                    stats[metric] = stat["value"] - self.prev_stats[metric]
                    self.prev_stats[metric] = stat["value"]

        global_data = json.loads(self.requestGlobalMetrics())
        for stat in global_data["data"][0]["stats"]:
            if stat["name"] in global_desired_stats:
                metric = str(stat["name"])
                stats[metric] = stat["value"] - self.prev_stats[metric]
                self.prev_stats[metric] = stat["value"]

        try:
            f = open("tmp-" + self.prefix + ".json", 'w')
            f.write("stats:>" + str(stats) + "\n")
        finally:
            f.close()

def signal_handler(sig, frame):
    for client in clients:
        client.unregister()
    sys.exit(0)

if __name__ == "__main__":

    num_instances = 2
    file_path = ""
    if (len(sys.argv) == 2):
        file_path = sys.argv[1]
    else:
        print("Warning - No filepath passed, using defaults (" + DEFAULT_FP + " plus num of intance).")
        file_path = DEFAULT_FP

    signal.signal(signal.SIGINT, signal_handler)

    for instance in range(0, num_instances):
        client = Client()
        client.getFilepath(file_path + str(instance))
        client.getPrefix("l" + str(instance+1))
        client.register()
        client.initMetrics()
        clients.append(client)

    while 1:
        for client in clients:
            client.getMetrics()
            os.rename("tmp-" + client.prefix + ".json", 'telemetry_stats' + client.prefix + '.json')

        time.sleep(5)
