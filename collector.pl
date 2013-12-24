use bigint;
use LWP::UserAgent;
use JSON -support_by_pp;
use Config::IniFiles;
use POSIX qw(strftime);

# required for --log-master
STDOUT->autoflush(1);

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $cfg = Config::IniFiles->new( -file => "/etc/uwsgi/local.ini" );

my $base_url = 'https://'.$cfg->val('uwsgi', 'api_domain').'/api';
my $ssl_key = $cfg->val('uwsgi', 'api_client_key_file');
my $ssl_cert = $cfg->val('uwsgi', 'api_client_cert_file');

sub collect_metrics {
	my ($uid) = @_;
	collect_metrics_cpu($uid);
	collect_metrics_io($uid);
	collect_metrics_mem($uid);
	#collect_metrics_net($uid);
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

	foreach(@{$containers}) {
		collect_metrics($_->{uid});
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
