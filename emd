#!/usr/local/bin/perl

# emd -- email disposer.
#
# it's a program for receiving mails were obtained by your
# mail-fetch program (`emo`, as an example) pipe them
# into mail-formatter (such as emp) and finally dispose them
# (i.e. pick an appropriate file for them to be stored in).
# it also can notify you by the means of a particular program
# you pick to be notified with (consider xmessage(1)).
# 
# its behaviour is controlled via config file, located in ~/.emdrc.


use strict;
use IPC::Open2;


# predefined variables for config (and for the script as well).
my $HOME = $ENV{HOME};
my $USER = $ENV{USER};

# path to a config file.
my $config_path = "$HOME/.emdrc";

# it may be asked in the config notifier entry.
my $sender_addr = "";

# the place where the mail will go.
my $out_filename = "";

# are we inside mail headers?
my $headers = 0;

# what we'll print to the disposition file.
my $final_output = "";

# a configuration (all the field are optional, actually):
#  - vars -- variables that may be further used in configuration
#            after their declaration. there are some predefined of
#            them, as you can see.
#  - formatter -- a program doing email formatting (processing).
#  - default -- a default disposition (post office/inbox) for a mail.
#               it's also a final destination for letters didn't match
#               any filters ("rules", as they're called in the config).
#  - notifier -- a program which does notifying us about incoming mail.
#  - rules -- filter rules for mails. it does filtering only depends on
#             header fields. it consists of a perl-style regex with the
#             disposition file path following.
# lines starting with "#" are comments and ignored.
my %config = (
	"vars" => {
		"HOME" => $HOME,
		"USER" => $USER,
	},
	"formatter" => "/usr/local/bin/emp",
	"default" => "/var/mail/$USER",
	"notifier" => undef,
	"rules" => undef
);

# notify us about mail has been received (assume you use emd as your
# mda), processed and disposed (if it's turned on if the config file).
# inside the "notifier" value (which is the command will be invoked),
# we can use special notifier variables and constructions, which are:
#  - &addr -- a sender's mail (from who we got an email from).
#  - &inbox -- a file where the message goes.
#  - {...} -- inside curly braces you can specify stuff that will
#             be sent to a program only in case mail disposition
#             file differs from the default.
sub notify {
	my $notifier = $config{notifier};

	if (not $notifier) {
		return;
	}
	if ($out_filename eq $config{default}) {
		$notifier =~ s/{.*}//g;
	} else {
		$notifier =~ s/{(.*)}/\1/g;
	}
	$notifier =~ s/\&addr/$sender_addr/g;
	$notifier =~ s/\&inbox/$out_filename/g;
	$notifier =~ s/\\n/\n/g;
	exec $notifier;
}

# handle config variables (the ones that start from "$").
sub substitute_vars {
	my ($line) = @_;
	if ($line =~ /\$(\w+)/) {
		my $var = $1;
		my $var_val = $config{vars}{$var};
		$line =~ s/\$\w+/$var_val/g;
	}
	return $line;
}

# extract config values from the config file.
sub parse_config {
	my $is_config = open(CONFIG, "$config_path");
	if (not $is_config) {
		return;
	}
	while (my $line = <CONFIG>) {
		# ignore comment lines.
		if ($line =~ /^#/) {
			next;
		}
		# get formatter.
		if ($line =~ /formatter\s=>\s(.*)/) {
			$config{formatter} = substitute_vars($1);
			next;
		}
		# get default inbox.
		if ($line =~ /default\s=>\s(.*)/) {
			$config{default} = substitute_vars($1);
			next;
		}
		# get a string for notifier execution.
		if ($line =~ /notifier\s=>\s(.*)/) {
			$config{notifier} = substitute_vars($1);
			next;
		}
		# get and save variable names and values.
		if ($line =~ /\$(\w+)\s=\s(.*)/) {
			$config{vars}->{$1} = substitute_vars($2);
			next;
		}
		# handle and save rules.
		if ($line =~ /(\/.*\/.*)\s=>\s(.*)/) {
			my $pattern = $1;
			my $path = substitute_vars($2);
			push (@{$config{rules}}, {$pattern => $path});
			next;
		}
	}
}

parse_config();

# now, only after config has been parsed, we save the
# default inbox name.
$out_filename = $config{default};


# in order to pass our standard input to formatters stdin and
# then read the output from it, we need to open the program file
# both for reading and writing. here the `open2` we have.
open2(\*FORMATTER_OUT, \*FORMATTER_IN, $config{formatter})
	or die "[emd]: Can't execute mail formatter you specified:",
	" $config{formatter}.\n";

# pass or stdin to stdin of out formatter.
print FORMATTER_IN <STDIN>;

# don't forget to close the *input* filehandle when we're done.
close (FORMATTER_IN);


# now we can read the formatter output using *output* filehandle.
while ( my $line = <FORMATTER_OUT> ) {
	# first of all, we need to tell if we're inside letter headers.
	# 'cause if we are, then we must start checking filter rules.
	if ($line =~ /^From\s/) {		
		$headers = 1;
		goto save_and_next;
	}
	if ($headers) {
		if ($line eq "\n") {
			$headers = 0;
			goto save_and_next;
		}
		# can take it as is, 'cause we've just piped a raw mail
		# into formatter, thus it mustn't be encoded (if the formatter's nice,
		# like emp).
		# keep in mind, that sender's address may not be enclosed
		# within angle brackets.
		if (
			$line =~ /^From:\s.*\<(.*)\>/
			or $line =~ /^From: ([^<]*)\n/
		) {
			$sender_addr = $1;
		}
		# checking the rules.
		for my $rule (@{$config{rules}}) {
			my %rule = %{$rule};
			for my $pattern (keys %rule) {
				my $pattern_regex ;
				my $regex_mod;
				if ($pattern =~ /\/(.*)\/(.*)/) {
					$pattern_regex = $1;
					$regex_mod = $2;
				}
				# complain if the pattern doesn't actually is a valid
				# perl-like regex. but don't die, just skip it.
				else {
					print STDERR "[emd]: wrong pattern specified: $pattern.\n";
					next;
				}
				# determine the final destination of a file depending
				# on rule matches. if neither match, the default it is.
				my $regex = qr/(?$regex_mod)$pattern_regex/;
				if ($line =~ $regex) {
					$out_filename = $rule{$pattern};
				}
			}
		}
	}
	# we want to print an entire mail anyway.
	save_and_next:
	$final_output .= "$line";
}

# open disposition file and append mail to it.
open(OUT, ">> $out_filename")
	or die "[emd]: can't open a disposition file: $out_filename\n";

print OUT $final_output;

# invoke notification program (specified in config), if it is.
notify();
