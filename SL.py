

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--spines", type=int, action="store", dest="spines",
    help="Number of spines. This cannot be used with --leaves as it will automatically calculate the number of spines. Example: --spines=4")
parser.add_argument("--leaves", type=int, action="store", dest="leaves",
    help="Number of leaves. This cannot be used with --spines as it will automatically calculate the number of leaves Example: --leaves=16")
parser.add_argument("--spine-speed", type=int, action="store", dest="spine_speed",
    help="Speed of network ports in spine (1,10,40,100) Example: --spine-speed=40")
parser.add_argument("--spine-ports", type=int, action="store", dest="spine_ports",
    help="Number of network ports in spine Example: --spine-ports=16")
parser.add_argument("--leaf-down-speed", type=int, action="store", dest="leaf_down_speed",
    help="Speed of server-facing ports on the leaf (1,10,40,100) Example: --leaf-down-speed=10")
parser.add_argument("--leaf-down-ports", type=int, action="store", dest="leaf_down_ports",
    help="Number of server-facing ports Example: --leaf-down-ports=48")
parser.add_argument("--leaf-up-speed", type=int, action="store", dest="leaf_up_speed",
    help="Speed of spine-facing ports on the leaf (1,10,40,100) Example: --leaf-up-speed=40")
parser.add_argument("--leaf-up-ports", type=int, action="store", dest="leaf_up_ports",
    help="Number of spine-facing ports Example: --leaf-up-ports=4")
parser.add_argument("-b", "--base-prefix", action="store", dest="base_prefix",
    help="Base prefix and mask to be used to assign L3 addresses. Example --base-prefix=192.168/16")
parser.add_argument("-p", "--p2p-mask", type=int, action="store", dest="p2p_mask",
    help="Network mask to use when calculating p2p networks. Value must be between 24 and 31")
parser.add_argument("-a", "--autonomous-system", type=int, action="store", dest="autonomous_system",
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

#def handle_options:



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
