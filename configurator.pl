use LWP::UserAgent;
use JSON;
use Config::IniFiles;
use POSIX qw(strftime);

# required for --log-master
STDOUT->autoflush(1);

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $cfg = Config::IniFiles->new( -file => "/etc/uwsgi/local.ini" );

my $base_url = 'https://'.$cfg->val('uwsgi', 'api_domain').'/api/private';
my $ssl_key = $cfg->val('uwsgi', 'api_client_key_file');
my $ssl_cert = $cfg->val('uwsgi', 'api_client_cert_file');

my $timeout = 30;

for(;;) {
	my $ua = LWP::UserAgent->new;
	$ua->ssl_opts(
		SSL_key_file => $ssl_key,
		SSL_cert_file => $ssl_cert,
	);
	$ua->timeout($timeout);

	my $response =  $ua->get($base_url.'/containers/');

	if ($response->is_error or $response->code != 200 ) {
		print date().' oops: '.$response->code.' '.$response->message."\n";
		exit;
	}

	my $containers = decode_json($response->decoded_content);

	my %available_container = {};
	
	foreach(@{$containers}) {
		my $vassal = '/etc/uwsgi/vassals/'.$_->{uid}.'.ini';
		if (-f $vassal) {
			my @st = stat($vassal);
			if ($_->{mtime} > $st[9]) {
				get_ini($_->{uid}, $vassal);
			}
			# if the .ini is ok, check only for ssh keys
			else {
				my $authorized_keys = '/containers/'.$_->{uid}.'/.ssh/uwsgi_authorized_keys';
				my @st = stat($authorized_keys);
				if ($_->{ssh_keys_mtime} > $st[9]) {
                                	get_ssh_keys($_->{uid}, $authorized_keys);
                        	}
			}
		}
		else {
			get_ini($_->{uid}, $vassal);
		}
		$available_container{$_->{uid}.'.ini'} = $_->{uid};
	}

	opendir DIR,'/etc/uwsgi/vassals';
	@files = readdir(DIR);
	closedir(DIR);

	foreach(@files) {
		next if /^\./;
		next if /^30000\.ini$/;
		next unless /^3\d+\.ini$/;
		unless(exists($available_container{$_})) {
			unlink '/etc/uwsgi/vassals/'.$_;
			print date().' '.$_." removed\n";
		}
	}

	my $reconfigure_firewall = 0;

	$response =  $ua->get($base_url.'/legion/nodes/');
	if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }

	my $legion_nodes = decode_json($response->decoded_content);
	my $etc_uwsgi_legion_nodes = '/etc/uwsgi/legion_nodes';
	if (-f $etc_uwsgi_legion_nodes) {
		my @st = stat($etc_uwsgi_legion_nodes);
		if ($legion_nodes->{unix} > $st[9]) {
			update_nodes($etc_uwsgi_legion_nodes, $legion_nodes->{'nodes'});
			$reconfigure_firewall = 1;
		}
	}
	else {
		update_nodes($etc_uwsgi_legion_nodes, $legion_nodes->{'nodes'});
		$reconfigure_firewall = 1;
	}


	$response =  $ua->get($base_url.'/nodes/');
        if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }

        my $nodes = decode_json($response->decoded_content);
        my $etc_uwsgi_nodes = '/etc/uwsgi/nodes';
        if (-f $etc_uwsgi_nodes) {
                my @st = stat($etc_uwsgi_nodes);
                if ($nodes->{unix} > $st[9]) {
                        update_nodes($etc_uwsgi_nodes, $nodes->{'nodes'});
			$reconfigure_firewall = 1;
                }
        }
        else {
                update_nodes($etc_uwsgi_nodes, $nodes->{'nodes'});
		$reconfigure_firewall = 1;
        }

	# get the list of custom services (if any...)
	$response =  $ua->get($base_url.'/custom_services/');
	if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }
	my $services = decode_json($response->decoded_content);
	my %available_custom_services = {};
	foreach(@{$services}) {
		my $vassal = '/etc/uwsgi/custom_services/'.$_->{customer}.'_'.$_->{id}.'.ini';
                if (-f $vassal) {
                        my @st = stat($vassal);
                        if ($_->{mtime} > $st[9]) {
                                write_ini($vassal, $_->{config});
                        }
                }
                else {
			write_ini($vassal, $_->{config});
                }
                $available_custom_services{$_->{customer}.'_'.$_->{id}.'.ini'} = $_->{id}
	}
	opendir DIR,'/etc/uwsgi/custom_services';
        @files = readdir(DIR);
        closedir(DIR);

        foreach(@files) {
                next if /^\./;
                next unless /\d+_\d+\.ini$/;
                unless(exists($available_custom_services{$_})) {
                        unlink '/etc/uwsgi/custom_services/'.$_;
                        print date().' '.$_." removed\n";
                }
        }

	
	

	if ($reconfigure_firewall) {
		system("sh /etc/uwsgi/firewall.sh");
	}

	# alarms;
	opendir ALARMS,'/etc/uwsgi/alarms';
	@alarms = readdir(ALARMS);
	closedir(ALARMS);

	foreach(@alarms) {
		next if /^\./;
		next if length($_) != 36 && length($_) != 40;
		# is it a zombie .tmp file ?
		if (length($_) == 40 && $_ =~ /\.tmp/) {
			my $filename = '/etc/uwsgi/alarms/'.$_;
			my @st = stat($filename);
                        if ($st[9] + 300 < time()) {
				print date()."unlinking zombie alarm file: ".$filename."\n";
				unlink $filename;	
                        }
			next;
		}	
		my $filename = '/etc/uwsgi/alarms/'.$_;
		open ALARM, $filename;
		binmode ALARM;
		my $alarm = <ALARM>;
		close ALARM;
		# just in case the json is broken...
		eval {
			my $j = decode_json($alarm);
			trigger_alarm($j->{container}, $j->{msg}, $j->{unix});
		};
		unlink $filename;
	}


	# portmappings
	$response = $ua->get($base_url.'/portmappings/');
        if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }

        my $portmappings = decode_json($response->decoded_content);
        my $etc_uwsgi_portmappings = '/etc/uwsgi/portmappings.sh';
	if (-f $etc_uwsgi_portmappings) {
		my @st = stat($etc_uwsgi_portmappings);
                if ($portmappings->{unix} > $st[9]) {
			update_portmappings($etc_uwsgi_portmappings, $portmappings->{'mappings'});
		}
	}
	else {
		update_portmappings($etc_uwsgi_portmappings, $portmappings->{'mappings'});
	}

	sleep(30);
}

sub get_ini {
	my ($uid, $vassal) = @_;

	my $ua = LWP::UserAgent->new;
	$ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout($timeout);

        my $response =  $ua->get($base_url.'/containers/'.$_->{uid}.'.ini');

	if ($response->is_error or $response->code != 200) {
                print date().' oops for '.$uid.': '.$response->code.' '.$response->message."\n";
		return;
        }

	my $ini = $response->decoded_content;

	open INI,'>'.$vassal;
	print INI $ini;
	close(INI);

	print date().' '.$vassal." updated\n";
};

sub get_ssh_keys {
	my ($uid, $authorized_keys) = @_;
	my $ua = LWP::UserAgent->new;
        $ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout($timeout);

        my $response =  $ua->get($base_url.'/ssh_keys/'.$_->{uid});	
	
	if ($response->is_error or $response->code != 200) {
                print date().' oops for '.$uid.': '.$response->code.' '.$response->message."\n";
                return;
        }

	my $keys = $response->decoded_content;

        open SSH,'>'.$authorized_keys;
        print SSH $keys."\n";
        close(SSH);

        print date().' '.$authorized_keys." updated\n";
}

sub date {
	return strftime "%Y-%m-%d %H:%M:%S", localtime;
}

sub update_nodes {
	my ($filename, $nodes) = @_;
	open LN,'>'.$filename;
	foreach(@{$nodes}) {
		print LN $_."\n";
	}
	close(LN);
}

sub update_portmappings {
	my ($filename, $mappings) = @_;
	open PM,'>'.$filename;
	print PM "iptables -t nat -F portmappings\n\n";
	foreach(@{$mappings}) {
		my $iptables = 'iptables -t nat -A portmappings -p '.$_->{proto}.' -d '.$_->{public_ip}.
				' --dport '.$_->{public_port}.' -j DNAT --to '.$_->{private_ip}.':'.$_->{private_port};
		print PM $iptables."\n";
	}
	close(PM);
	system('sh '.$filename);
}

sub write_ini {
	my ($vassal, $ini) = @_;
	open INI,'>'.$vassal;
        print INI $ini;
        close(INI);

        print date().' '.$vassal." updated\n";
}

sub trigger_alarm {
	my ($container, $msg, $unix) = @_;
	my $ua = LWP::UserAgent->new;
        $ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout($timeout);
	$response = $ua->post($base_url.'/alarms/'.$container.'?unix='.$unix, Content => $msg);
        if ($response->is_error or $response->code != 201 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
        }
}
