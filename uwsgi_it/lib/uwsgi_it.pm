package uwsgi_it;
use Dancer ':syntax';
use Data::Dumper;
use LWP::UserAgent;
use JSON qw/encode_json decode_json/;

STDOUT->autoflush(1);
$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $api_domain = 'api.uwsgi.it';
my $api_base = '/api';

our $VERSION = '0.1';

hook 'before' => sub {
	print "before2 ".request->path_info."\n";
	if (request->path ne '/login' && (!session('username') or !session('password'))) {
		redirect uri_for('/login');
	}
};

get '/' => sub {
	my $j = get_uwsgi_json(session('username'), session('password'), 'me/');
	unless ($j) {
		session->destroy;
		redirect uri_for('/login');
	}
	print "home\n";
	template 'home', {'customer' => $j};
};

any '/logout' => sub {
	session->destroy;
	redirect uri_for('/login');
};

get '/domains' => sub {
	my $j = get_uwsgi_json(session('username'), session('password'), 'domains/');
	template 'domains', {'domains' => $j};
};

post '/domains/add' => sub {
	my $j = {'name' => param('name')};
	post_uwsgi_json(session('username'), session('password'), $j, 'domains/');
	redirect uri_for('/domains');
};

post '/' => sub {
	print param('vat')."\n";
	print param('company')."\n";
	my $j = {'vat' => param('vat'), 'company' => param('company') };
	post_uwsgi_json(session('username'), session('password'), $j, 'me/');
	redirect uri_for('/');
};

get '/login' => sub {
	print "ciao\n";
	template 'index', {'login_url' => uri_for('/login')};
};

post '/login' => sub {
	print STDERR "H e l l o\n";
	print STDERR param('username')."\n";
	print STDERR param('password'),"\n";
	my $j = get_uwsgi_json(param('username'), param('password'), 'me/');
	print Dumper($j);
	if ($j) {
		session 'username' => param('username');
		session 'password' => param('password');
	}
	redirect uri_for('/');
};

sub get_uwsgi_json {
	my ($user, $password, $api) = @_;
	my $ua = LWP::UserAgent->new;
	$ua->credentials($api_domain.':443', 'uwsgi.it api', $user, $password);
	$ua->timeout(3);
	my $response = $ua->get('https://'.$api_domain.$api_base.'/'.$api);
	if ($response->is_success && $response->code =~ /^20\d$/) {
		if ($response->content_type eq 'application/json') {
			return decode_json($response->decoded_content);
		}
		return $response->decoded_content;
	}
	else {
		print $response->code.' '.$response->message."\n";
	}	
	return undef;
};

sub post_uwsgi_json {
        my ($user, $password, $j, $api) = @_;
        my $ua = LWP::UserAgent->new;
        $ua->credentials($api_domain.':443', 'uwsgi.it api', $user, $password);
        $ua->timeout(3);
        my $response = $ua->post('https://'.$api_domain.$api_base.'/'.$api, Content => encode_json($j));
        if ($response->is_success && $response->code =~ /^20\d$/) {
		if ($response->content_type eq 'application/json') {
                	return decode_json($response->decoded_content);
		}
		return $response->decoded_content;
        }
        else {
                print $response->code.' '.$response->message."\n";
        }
        return undef;
};


true;
