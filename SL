#!/usr/bin/perl -w
use strict;
use NetAddr::IP::Lite;
use Net::Netmask;
use Socket;
use Getopt::Long;
use POSIX qw/ceil/;
use JSON;

##
## Globals
##
my %options = ();
my %spine = ();
my %leaf = ();

##
## Main
##

handle_options();
calc_os();
generate_topology();

my %top = ();
$top{spine} = \%spine;
$top{leaf} = \%leaf;

my $json = JSON->new->allow_nonref->pretty;
$json->canonical(1);

print $json->encode(\%top);

##
## Functions
##
sub next_subnet
{
	my ($network, $subnet) = @_;

	my $inet = unpack 'N', pack 'CCCC', split /\./, $network;
	my $step = 1 << 32 - $subnet;

	my $next = $inet + $options{p2p_mask};

	$inet += $step;

	my $next_ip = sprintf "%vd", pack 'N', $inet;

	return $next_ip;
}

sub generate_topology
{
	my $spine_int = $options{spine_speed} == 10 ? 'xe' : 'et';
	my $block = new Net::Netmask($options{base_prefix});
	my $block_base = $block->base();
	my $p2p = $block_base;
	my $as = $options{as};

	for(my $s = 0; $s < $options{spines}; $s++)
	{
		$spine{$s}{name} = "S$s";
		$spine{$s}{as} = $as++;

		for(my $l = 0; $l < $options{leaves}; $l++)
		{
			my $ip = NetAddr::IP::Lite->new("$p2p/$options{p2p_mask}");
			my $ip_first = sprintf('%s', $ip->first());
			my $ip_last = sprintf('%s', $ip->last());

			$spine{$s}{port}{$l}{ifd} = "$spine_int-0/0/$l";
			$spine{$s}{port}{$l}{address} = $ip_first;

			$leaf{$l}{name} = "L$l";
			$leaf{$l}{port}{$s}{ifd} = "$spine_int-0/0/$s";
			$leaf{$l}{port}{$s}{address} = $ip_last;

			$p2p = next_subnet($p2p, $options{p2p_mask});

			exists $leaf{$l}{as} or $leaf{$l}{as} = $as++;
		}
	}
}

sub calc_os
{
	$options{os} = ($options{leaf_down_speed} * $options{leaf_down_ports}) / ($options{leaf_up_speed} * $options{leaf_up_ports});
}

sub usage
{
	my $str = shift;
	my $command = $0;

	$command =~ s/^\W+//;

	if(defined($str))
	{
		print STDERR $str;
	}

	print STDERR <<EOF;
Usage: $command <--spines=NUMBER || --leaves=NUMBER> --spine-speed=SPEED --spine-ports=NUMBER --leaf-down-speed=SPEED --leaf-down-ports=NUMBER --leaf-up-speed=SPEED --leaf-up-ports=NUMBER --base-prefix=PREFIX/MASK --p2p-MASK=MASK --autonomous-system=AS

  -h, --help			Display this help menu.
  --spines			Number of spines. This cannot be used with --leaves
				as it will automatically calculate the number of spines
					Example: --spines=4
  --leaves			Number of leaves. This cannot be used with --spines
				as it will automatically calculate the number of leaves
					Example: --leaves=16
  --spine-speed			Speed of network ports in spine (1,10,40,100)
					Example: --spine-speed=40
  --spine-ports			Number of network ports in spine
					Example: --spine-ports=16
  --leaf-down-speed		Speed of server-facing ports on the leaf (1,10,40,100)
					Example: --leaf-down-speed=10
  --leaf-down-ports		Number of server-facing ports
					Example: --leaf-down-ports=48
  --leaf-up-speed		Speed of spine-facing ports on the leaf (1,10,40,100)
					Example: --leaf-up-speed=40
  --leaf-up-ports		Number of spine-facing ports
					Example: --leaf-up-ports=4
  -a, --autonomous-system	Where to begin assigning autonomous system numbers.
					Example: --autonomous-system=64512
  -b, --base-prefix		Base prefix and mask to be used to assign L3 addresses.
					Example --base-prefix=192.168/16
  -p, --p2p-mask		Network mask to use when calculating p2p networks.
				Value must be between 24 and 31.
					Example --p2p-mask=30

Report $command bugs to doug\@juniper.net
EOF

	exit(1);
}

sub handle_options
{
	Getopt::Long::GetOptions(
		'help',			=> \$options{help},
		'spines=i',		=> \$options{spines},
		'leaves=i',		=> \$options{leaves},
		'spine-speed=i',	=> \$options{spine_speed},
		'spine-ports=i',	=> \$options{spine_ports},
		'leaf-down-speed=i',	=> \$options{leaf_down_speed},
		'leaf-down-ports=i',	=> \$options{leaf_down_ports},
		'leaf-up-speed=i',	=> \$options{leaf_up_speed},
		'leaf-up-ports=i',	=> \$options{leaf_up_ports},
		'base-prefix=s',	=> \$options{base_prefix},
		'p2p-mask=i',		=> \$options{p2p_mask},
		'autonomous-system=i',	=> \$options{as},
	) or usage();

	if(defined($options{help}))
	{
		usage();
	}

	# Make sure --spines and --leaves are used correctly.
	if(defined($options{leaves}) &&
		defined($options{spines}))
	{
		die("The options --spines and --leaves cannot be used together. If --spines is used, it will automatically calculate the number of leaves and vice versa.\n");
	}
	if(!defined($options{spines}) &&
		!defined($options{leaves}))
	{
		die("You must specify either --spines or --leaves\n");
	}

	# Make sure we have something
	if(!defined($options{spine_speed})) { usage("Please specify --spine-speed\n"); }
	if(!defined($options{spine_ports})) { usage("Please specify --spine-ports\n"); }
	if(!defined($options{leaf_down_speed})) { usage("Please specify --leaf-down-speed\n"); }
	if(!defined($options{leaf_down_ports})) { usage("Please specify --leaf-down-ports\n"); }
	if(!defined($options{leaf_up_speed})) { usage("Please specify --leaf-up-speed\n"); }
	if(!defined($options{leaf_up_ports})) { usage("Please specify --leaf-up-ports\n"); }
	if(!defined($options{base_prefix})) { usage("Please specify --base-prefix\n"); }
	if(!defined($options{p2p_mask})) { usage("Please specify --p2p-mask\n"); }
	if(!defined($options{as})) { usage("Please specify --autonomous-system\n"); }


	# Begin sanity checking
	if(defined($options{spines}))
	{
		if($options{spines} < 2)
		{
			die("The number of spines cannot be less than two.\n");
		}
	}
	if(defined($options{leaves}))
	{
		if($options{leaves} < 2)
		{
			die("The number of leaves cannot be less than two.\n");
		}
	}

	if($options{leaf_down_speed} < 1 || $options{leaf_down_speed} > 400)
	{
		die("The speed must be greater than 1 and less than 400.");
	}
	if($options{leaf_up_speed} < 1 || $options{leaf_up_speed} > 400)
	{
		die("The speed must be greater than 1 and less than 400.");
	}
	if($options{spine_speed} < 1 || $options{spine_speed} > 400)
	{
		die("The speed must be greater than 1 and less than 400.");
	}

	if($options{spine_ports} < 4)
	{
		die("The number of spine ports needs to be greater than four.\n");
	}
	if($options{leaf_up_ports} < 2)
	{
		die("The number of spine ports needs to be greater than two.\n");
	}

	if($options{spine_speed} != $options{leaf_up_speed})
	{
		die("The --spine-speed and --leaf-up-speed do not match.\n");
	}

	if($options{p2p_mask} < 24 || $options{p2p_mask} > 31)
	{
		die("--p2p-mask must be between 24 and 31.\n");
	}


	# We have to calculate the number of spines or leaves before continuing
	if(defined($options{spines}))
	{
		my $spine_links = $options{spines} * $options{spine_ports};

		$options{leaves} = ceil($spine_links / $options{leaf_up_ports});

		if($options{spines} > $options{leaf_up_ports})
		{
			die("The number of spines was specified as $options{spines}, but this exceeds the number of --leaf-up-ports($options{leaf_up_ports}) specified.\n");
		}
	}
	elsif(defined($options{leaves}))
	{
		my $leaf_links = $options{leaves} * $options{leaf_up_ports};

		$options{spines} = ceil($leaf_links / $options{spine_ports});

		if($options{spines} > $options{leaf_up_ports})
		{
			die("The number of spines was auto-calculated to $options{spines}, but this exceeds the number of --leaf-up-ports($options{leaf_up_ports}) specified.\nHint: try increasing the number of --spine-ports or --leaf-up-ports. Another possibility is to reduce the number of --leaves");
		}
	}
	else
	{
		die("This should never happen. You must either specify --spines or --leaves, but not both nor neither.\n");
	}

	# Sanity check to see if there's enough AS numbers
	{
		my $nodes = $options{spines} + $options{leaves};

		if($options{as} + $nodes > 65535)
		{
			my $recommendation = 65535 - ($nodes * 1.1);
			die("You specified an autonomous system of $options{as}, but there are a total of $nodes nodes in the topology ($options{spines} spines and $options{leaves} leaves) and this exceeds the maximum autonomous system number of 65535.\nHint: try using --autonomous-system=$recommendation\n");
		}

		if($options{as} < 1)
		{
			die("--autonomous-system has to be greater than or equal to 1.\n");
		}
	}

	# Sanity check the base prefix and p2p mask against the SL topology
	{
		my $block = new Net::Netmask($options{base_prefix});
		my $block_base = $block->base();
		my $block_mask = $block->bits();

		my $p2p_links = $options{leaf_up_ports} * $options{leaves};
		my $usable_links = 2**(32-$block_mask) / 2**(32-$options{p2p_mask});

		if($usable_links < $p2p_links)
		{
			print STDERR <<EOF;
Given that this topology has $options{spines} spines and $options{leaves} leaves, the total number of point-to-point links requiring L3 addressing is $p2p_links.

The prefix $block using a /$options{p2p_mask} for each point-to-point link only yields $usable_links usable networks. There isn't enough point-to-point networks given these constraints.

There are two ways to fix this problem:
	1) Use a larger block such as $block_base/16
	2) Reduce the point-to-point mask size.

Hint: try again with --base-prefix=$block_base/16
EOF

			exit(1);
		}
	}
}
