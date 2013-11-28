#!/usr/bin/python

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
