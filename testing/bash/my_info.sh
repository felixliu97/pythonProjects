#!/bin/bash

# Display the hostname of the system
hostname

# Display the operating system and system uptime
systeminfo | grep "OS Name"
systeminfo | grep "System Up Time"

# Display the memory and disk usage
wmic memorychip get capacity
wmic logicaldisk get size, freespace, name

# Display the network interfaces and IP addresses
ipconfig
