#!/usr/local/bin/perl

# emo -- email obtainer.
#
# this is a program for either simple fetching all the emails
# from the IMAP server or simple running a daemon, that will
# look for new (unread) emails on the server.
# in both cases messages are piped into specified mda.
# 
# please, have a look at this source code (it's rather simple) -
# it describes almost all the aspects you have to know to run
# this program.


use strict;
# you need Mail::IMAPClient cpan(1) module to run the program.
use Mail::IMAPClient;


# we accept a single option, indicating whether or not
# will we operate in a daemon mode ("-d").
my $option = $ARGV[0];
my $is_daemon = $option eq "-d";

# a variable that allows us to actually talk to IMAP server.
my $imap;

# `$HOME` variable is also used in variables substitution.
# (see `sub_vars` function).
my $HOME = $ENV{HOME};
my $config_path = "$HOME/.emorc";

# variables, that will be issued in `sub_vars`.
my %vars = (
	"HOME" => $HOME
);

# a program configuration. it's populated via both
# front-end config file (hardcoded ~/.emorc) and,
# so-to-speak, shadow configuration file, which is also
# referred to as passfile, a file, containing your
# e-mail credentials. path to this shadow file is
# specified in the main config file.
#
# a little about properties themselves:
# 	- passfile -- path to a passfile (see above).
#	- serv -- an IMAP server we want to talk to.
#	- login -- your login.
#	- password -- your password.
#	- mda -- an MDA (Mail Delivery(Disposition I prefer) Agent)
#	         program we will pass incoming messages through.
#	         By default, it's `emd` utility.
#	- interval -- when invoced as a daemon (see `is_daemon`),
#	              this field specifies an interval for this
#	              daemon to wait until it will check for new
#	              (unseen) emails again.
# all those properties are specified like this (drop brackets):
#	`<property> => <value>`
#
# as for the passfile: in consists of these lines:
# 	`serv <your IMAP server>`
#	`login <your login>`
#	`password <password>`
#
# if any of `serv`, `login` or `password` fields would not be
# eventually filled, the program dies.
my %config = (
	passfile => undef,
	serv => undef,
	login => undef,
	password => undef,
	mda => "/usr/local/bin/emd",
	interval => 60
);


# substitute variables in main config file.
# it will not be called during parsing the passfile.
sub sub_vars {
	my ($line) = @_;
	if ($line =~ /\$(\w+)/) {
		my $var = $1;
		my $var_val = $vars{$var};
		$line =~ s/\$\w+/$var_val/g;
	}
	return $line;
}

# parse main config file (~/.emorc).
sub parse_config {
	my $is_config = open(CONFIG, "$config_path");
	if (!$is_config) {
		die "[emo]: a presence of a config file",
			"(~/.emorc) is required.\n";
	}
	while (my $line = <CONFIG>) {
		# lines started with "#" are commented and ignored.
		if ($line =~ /^#/) {
			next;
		}
		if ($line =~ /pass\s=>\s(.*)/) {
			$config{passfile} = sub_vars($1);
			next;
		}
		if ($line =~ /mda\s=>\s(.*)/) {
			$config{mda} = sub_vars($1);
			next;
		}
		if ($line =~ /interval\s=>\s(.*)/) {
			$config{interval} = sub_vars($1);
			next;
		}
	}
}

# pass shadow passfile.
# keep writing to a `%config` variable.
sub parse_passfile() {
	my $is_passfile = open(PASS, "$config{passfile}");
	if (!$is_passfile) {
		die "[emo]: can't open a passfile you specified:",
			"$config{passfile}.\n";
	}
	while (my $line = <PASS>) {
		# for the sake of simplicity, we do not support commented
		# lines here. And I also suppose we don't need variables here.
		if ($line =~ /^serv\s(.*)/) {
			$config{serv} = "$1";
			next;
		}
		if ($line =~ /^login\s(.*)/) {
			$config{login} = "$1";
			next;
		}
		if ($line =~ /^password\s(.*)/) {
			$config{password} = "$1";
			next;
		}
	}
}

# check if our program configuration was filled appropriately.
sub validate_config {
	if (not $config{serv}
		or not $config{login}
		or not $config{password}
	) {
    	die "[emo]: either server, login or password are not",
			"specified in the passfile ($config{passfile}).\n";
	}
	if (! -f $config{mda}) {
		die "[emo]: an MDA you specified is not a regular file: ",
			"$config{mda}.\n";
	}
}

# actually, pipe messages (read them first) into an MDA.
# both grab and daemon modes use this subroutine.
sub dispose_msgs {
	my (@msgs) = @_;
	my $total = $#msgs + 1;
	for my $idx (0 .. $#msgs) {
		my $msg_idx = $msgs[$idx];
		open(MDA, "|-", "$config{mda}")
			or die "[emo]: Can't open an MDA program you specified: ",
				"$config{mda}.\n";
		my $msg = $imap->message_string($msg_idx, 1);
		$msg =~ s/\r\n/\n/g;
		print MDA $msg;
		close(MDA);
		print "[emo]: mails obtained: @{[$idx+1]}/$total.\n";
	}
}

# grab mode basically means that all the mails from "INBOX"
# folder will be obtained from the server. once that's done
# the program finishes.
sub grab_mode {
	my @msgs = $imap->search("ALL");
	dispose_msgs @msgs;
}

# a daemon mode, on the other hand, will periodically
# check the server for new (unseen) mails and dispose
# them as well.
sub daemon_mode {
	while (1) {
		# handle connection time out.
		while (!$imap->noop) {
			# try to reconnect;
			$imap->reconnect;
			# now check the result of our attempt.
			if ($imap->IsConnected()) {
				# we're connected. cool.
				last;
			}
			else {
				# try again after a while.
				sleep 1;
			}
		}
		my @msgs = $imap->search("UNSEEN");
		dispose_msgs @msgs;
		sleep $config{interval};
	}
}


# first of all, we parse the configs.
parse_config();
parse_passfile();

# and validate them.
validate_config();


# now, create a connection to IMAP server, using the
# data from the configuration.
$imap = Mail::IMAPClient->new(
	Server => $config{serv},
	User => $config{login},
	Password => $config{password},
	Ssl => 1,
	Uid => 0,
	IgnoreSizeErrors => 1
) or die "[emo]: Could not connect to $config{serv}, ",
	"terminating... $@\n";

# all the operations are perform on "INBOX" folder.
$imap->select("INBOX");

# and then, depending on our mode (option was specified)
# we do our job.
if ($is_daemon) {
	daemon_mode();
} else {
	grab_mode();
}
