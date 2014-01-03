use LWP::UserAgent;
use JSON;
use Config::IniFiles;
use POSIX qw(strftime);

# required for --log-master
STDOUT->autoflush(1);

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $cfg = Config::IniFiles->new( -file => "/etc/uwsgi/local.ini" );

my $base_url = 'https://'.$cfg->val('uwsgi', 'api_domain').'/api';
my $ssl_key = $cfg->val('uwsgi', 'api_client_key_file');
my $ssl_cert = $cfg->val('uwsgi', 'api_client_cert_file');

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

	my %available_container = {};
	
	foreach(@{$containers}) {
		my $vassal = '/etc/uwsgi/vassals/'.$_->{uid}.'.ini';
		if (-f $vassal) {
			my @st = stat($vassal);
			if ($_->{mtime} > $st[9]) {
				get_ini($_->{uid}, $vassal);
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
		next unless /^3\d+.ini$/;
		unless(exists($available_container{$_})) {
			unlink '/etc/uwsgi/vassals/'.$_;
			print date().' '.$_." removed\n";
		}
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
        $ua->timeout(3);

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

sub date {
	return strftime "%Y-%m-%d %H:%M:%S", localtime;
}
