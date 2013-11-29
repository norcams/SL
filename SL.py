#!/usr/bin/python

#import pdb

import argparse
import math
from IPy import IP

import sys
from socket import inet_aton

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--spines", type=int, action="store", dest="spines",
    help="Number of spines. This cannot be used with --leaves as it will automatically calculate the number of spines. Example: --spines=4")
group.add_argument("--leaves", type=int, action="store", dest="leaves",
    help="Number of leaves. This cannot be used with --spines as it will automatically calculate the number of leaves Example: --leaves=16")
parser.add_argument("--spine-speed", type=int, action="store", dest="spine_speed", required=True,
    help="Speed of network ports in spine (1,10,40,100) Example: --spine-speed=40")
parser.add_argument("--spine-ports", type=int, action="store", dest="spine_ports", required=True,
    help="Number of network ports in spine Example: --spine-ports=16")
parser.add_argument("--leaf-down-speed", type=int, action="store", dest="leaf_down_speed", required=True,
    help="Speed of server-facing ports on the leaf (1,10,40,100) Example: --leaf-down-speed=10")
parser.add_argument("--leaf-down-ports", type=int, action="store", dest="leaf_down_ports", required=True,
    help="Number of server-facing ports Example: --leaf-down-ports=48")
parser.add_argument("--leaf-up-speed", type=int, action="store", dest="leaf_up_speed", required=True,
    help="Speed of spine-facing ports on the leaf (1,10,40,100) Example: --leaf-up-speed=40")
parser.add_argument("--leaf-up-ports", type=int, action="store", dest="leaf_up_ports", required=True,
    help="Number of spine-facing ports Example: --leaf-up-ports=4")
parser.add_argument("-b", "--base-prefix", action="store", dest="base_prefix", required=True,
    help="Base prefix and mask to be used to assign L3 addresses. Example --base-prefix=192.168/16")
parser.add_argument("-p", "--p2p-mask", type=int, action="store", dest="p2p_mask", required=True,
    help="Network mask to use when calculating p2p networks. Value must be between 24 and 31")
parser.add_argument("-a", "--autonomous-system", type=int, action="store", dest="asn", required=True,
    help="Where to begin assigning autonomous system numbers. Example: --autonomous-system=64512")
options = parser.parse_args()

##
## Functions
##
def next_subnet (network, subnet):
	inet = IP2Int(network)
	step = 1 << 32 - subnet
	inet = inet + step
	next_ip = Int2IP(inet)
	return (next_ip)



#def generate_topology:

#def calc_os:

#def usage:

def sanitycheck_options( options ):
	# Begin sanity checking
	if options.spines:
		if options.spines < 2:
			raise Exception("The number of spines cannot be less than two.\n")
	if options.leaves:
		if options.leaves < 2:
			raise Exception("The number of leaves cannot be less than two.\n")
	if options.leaf_down_speed < 1 | options.leaf_down_speed > 400:
		raise Exception("The speed must be greater than 1 and less than 400.")
	if options.leaf_up_speed < 1 | options.leaf_up_speed > 400:
		raise Exception("The speed must be greater than 1 and less than 400.")
	if options.spine_speed < 1 | options.spine_speed > 400:
		raise Exception("The speed must be greater than 1 and less than 400.")
	if options.spine_ports < 4:
		raise Exception("The number of spine ports needs to be greater than four.\n")
	if options.leaf_up_ports < 2:
		raise Exception("The number of spine ports needs to be greater than two.\n")
	if options.spine_speed != options.leaf_up_speed:
		raise Exception("The --spine-speed and --leaf-up-speed do not match.\n")
	if options.p2p_mask < 24 | options.p2p_mask > 31:
		raise Exception("--p2p-mask must be between 24 and 31.\n")

	# We have to calculate the number of spines or leaves before continuing
	if options.spines:
		spine_links = options.spines * options.spine_ports
		options.leaves = int(math.ceil(spine_links / options.leaf_up_ports))
		if options.spines > options.leaf_up_ports:
			raise Exception("The number of spines was specified as elif options.spines}, but this exceeds the number of --leaf-up-ports(%s) specified.\n" % options.leaf_up_ports)

	elif options.leaves:
		leaf_links = options.leaves * options.leaf_up_ports
		options.spines = math.ceil(leaf_links /  options.spine_ports)

		if options.spines > options.leaf_up_ports:
			raise Exception("The number of spines was auto-calculated to elif options.spines}, but this exceeds the number of --leaf-up-ports(elif options.leaf_up_ports}) specified.\nHint: try increasing the number of --spine-ports or --leaf-up-ports. Another possibility is to reduce the number of --leaves") #NEED_CLEAN
	else:
		raise Exception("This should never happen. You must either specify --spines or --leaves, but not both nor neither.\n")

	# Sanity check to see if there's enough AS numbers
	#
	# NEED_FIX: This code needs to be modified to support 4Byte AS
	nodes = options.spines + options.leaves
	if options.asn + nodes > 65535:
		recommendation = 65535 - (nodes * 1.1)
		raise Exception("You specified an autonomous system of %s, but there are a total of %s nodes in the topology (%s spines and %s leaves) and this exceeds the maximum autonomous system number of 65535.\nHint: try using --autonomous-system=%s\n" % options.asn, nodes, options.spines, options.leaves, recommendation)
	if options.asn < 1:
		raise Exception("--autonomous-system has to be greater than or equal to 1.\n")

	# Sanity check the base prefix and p2p mask against the SL topology
	block_base = str(IP(options.base_prefix, make_net=True).net())
	block_mask_tmp = options.base_prefix.split('/', 1)
	block_mask = int(block_mask_tmp[1])

	p2p_links = int(options.leaf_up_ports * options.leaves)
	usable_links = 2**(32 - block_mask) / 2**(32 - options.p2p_mask)

	#pdb.set_trace()

	if usable_links < p2p_links: # NEED_FIX: Gotta sort out the problem with this Format String
		raise Exception("Given that this topology has %i spines and %i leaves, the total number of point-to-point links requiring L3 addressing is %i.\n \
The prefix %s using a /%i for each point-to-point link only yields %i usable networks. There isn't enough point-to-point networks given these constraints.\n\
There are two ways to fix this problem:\n\
\t1) Use a larger block such as %s/16\n\
\t2) Reduce the point-to-point mask size.\n\n\
Hint: try again with --base-prefix=%s/16" % (options.spines, options.leaves, p2p_links, options.base_prefix, options.p2p_mask, usable_links, block_base, block_base) )


def clos (in_spine, in_leaf):
	clos = {spine: in_spine, leaf: in_leaf}
	return clos

# IP2Int and Int2IP are taken from http://stackoverflow.com/questions/5619685/conversion-from-ip-string-to-integer-and-backward-in-python

def IP2Int(ip):
    o = map(int, ip.split('.'))
    res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
    return res

def Int2IP(ipnum):
    o1 = int(ipnum / 16777216) % 256
    o2 = int(ipnum / 65536) % 256
    o3 = int(ipnum / 256) % 256
    o4 = int(ipnum) % 256
    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()


sanitycheck_options(options)
