use bigint;
use LWP::UserAgent;
use JSON -support_by_pp;
use Config::IniFiles;
use POSIX qw(strftime);
use IO::Socket::INET;
use Quota;

# required for --log-master
STDOUT->autoflush(1);

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $cfg = Config::IniFiles->new( -file => "/etc/uwsgi/local.ini" );

my $base_url = 'https://'.$cfg->val('uwsgi', 'api_domain').'/api';
my $ssl_key = $cfg->val('uwsgi', 'api_client_key_file');
my $ssl_cert = $cfg->val('uwsgi', 'api_client_cert_file');

my $quota = Quota::getqcarg($cfg->val('uwsgi', 'api_hd'));

sub collect_metrics {
	my ($uid, $net_json) = @_;
	collect_metrics_cpu($uid);
	collect_metrics_io($uid);
	collect_metrics_mem($uid);
	collect_metrics_quota($uid);
	if ($net_json) {
		collect_metrics_net($uid, $net_json);
	}
}

sub collect_metrics_cpu {
	my ($uid) = @_;
	open CGROUP,'/sys/fs/cgroup/'.$uid.'/cpuacct.usage';
	my $value = <CGROUP>;
	close CGROUP;	
	chomp $value;
	push_metric($uid, 'container.cpu', $value);
}

sub collect_metrics_mem {
        my ($uid) = @_;
        open CGROUP,'/sys/fs/cgroup/'.$uid.'/memory.usage_in_bytes';
        my $value = <CGROUP>;
        close CGROUP;
        chomp $value;
        push_metric($uid, 'container.mem', $value);
}

sub collect_metrics_quota {
        my ($uid) = @_;
	my ($blocks,$soft,$hard) = Quota::query($quota, $uid);
        push_metric($uid, 'container.quota', $hard);
}

sub collect_metrics_net {
	my ($uid, $tuntap) = @_;
	my $peers = $tuntap->{peers};
	foreach(@{$peers}) {
		if ($_->{uid} == $uid) {
			push_metric($uid, 'container.net.rx', $_->{rx});
			push_metric($uid, 'container.net.tx', $_->{tx});
			return;
		}
	}
}

sub collect_metrics_io {
	my ($uid) = @_;
	my $r = Math::BigInt->new('0');
	my $w = Math::BigInt->new('0');

	open CGROUP,'/sys/fs/cgroup/'.$uid.'/blkio.io_service_bytes';
	while(<CGROUP>) {
		chomp;
		my ($device, $type, $value) = split /\s+/;
		if ($type eq 'Read') {
			my $r0 = Math::BigInt->new($value);
			$r += $r0;
		}
		elsif ($type eq 'Write') {
			my $w0 = Math::BigInt->new($value);
			$w += $w0;
		}
	}
	close CGROUP;

	push_metric($uid, 'container.io.read', $r);
	push_metric($uid, 'container.io.write', $w);
}

for(;;) {
	my $ua = LWP::UserAgent->new;
	$ua->ssl_opts(
		SSL_key_file => $ssl_key,
		SSL_cert_file => $ssl_cert,
	);
	$ua->timeout(3);

	my $response =  $ua->get($base_url.'/containers/');

	if ($response->is_error or $response->code != 200 ) {
		print date().' oops: '.$response->code.' '.$response->message."\n";
		exit;
	}

	my $containers = decode_json($response->decoded_content);

	my $net_json = undef;
	# get json stats from the tuntap router
	my $s = IO::Socket::INET->new(PeerAddr => '127.0.0.1:5001');
	if ($s) {
		my $tuntap_json = '';
		for(;;) {
			$s->recv(my $buf, 8192);
			last unless $buf;
			$tuntap_json .= $buf;
		}
		$net_json = decode_json($tuntap_json);	
	}


	foreach(@{$containers}) {
		collect_metrics($_->{uid}, $net_json);
	}

	sleep(60);
}

sub date {
	return strftime "%Y-%m-%d %H:%M:%S", localtime;
}

sub push_metric {
	my ($uid, $path, $value) = @_;

	my $ua = LWP::UserAgent->new;
        $ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout(3);

	my $j = JSON->new;
	$j->allow_bignum(1);
	$j = $j->encode({unix => time, value => Math::BigInt->new($value)});

	my $response =  $ua->post($base_url.'/metrics/'.$path.'/'.$uid, Content => $j);

	if ($response->is_error or $response->code != 201 ) {
                print date().' oops for '.$path.'/'.$uid.': '.$response->code.' '.$response->message."\n";
        }
}
