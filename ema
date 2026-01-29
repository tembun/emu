#!/usr/local/bin/perl

# ema -- extract email attachments into files.
#
# as stdin it accepts a mail, formatted via `emp` and
# uses `emb` in order to extract attachments from it
# and finaly distribute (actually, put in your filesystem) them.
# As a destination path it uses /tmp/ema/<current timestamp>/<name>,
# where <name> is an attachment name as it specified in the letter.
#
# if desired, particular attachment indexes for extracting
# may be specified as arguments.
#
# it has a special argument "l", which turns the program into
# list mode, in which it only prints all the found attachments
# in the message with their indexes for picking (they're actually
# the same ones that `emb` uses).


use strict;
# for bidirectional file opening.
use IPC::Open2;
# for figuring out current time.
use Time::Piece;
# for creating directories (nested) for the resulting files.
use File::Path qw(make_path);
# for encoding the attachments themselves.
use MIME::Base64;


# Global constants.
my $emb_path = "/usr/local/bin/emb";
my $ts = localtime->strftime('%H-%M-%S');
my $dest_dir = "ema/$ts";
my $dest = "/tmp/$dest_dir";


# Global variables.

my $stdin = "";

# if "l" specified as a first argument, then
# we show all the attachments in the letter
# (using `emb` output format).
my $list_mode = @ARGV[0] eq "l";

# if we're not in the list mode - save potential
# indexes to extract.
my @which;
if (not $list_mode) {
	@which = @ARGV;
}

# use it as mark that at least one attachment
# was found, hence we don't need to create a
# destination directory (common for all attachments) again.
my $att_found = 0;


# save standard input into variable to be able to re-use it.
while (my $line = <STDIN>) {
	$stdin .= $line;
}

# open `emb` utility for both reading and writing.
open2(\*EMB_OUT, \*EMB_IN, $emb_path)
			or die "[ema]: can't open $emb_path.";

# send our stdin into `emb`.
print EMB_IN "$stdin";
close (EMB_IN);


# main loop. reading output from `emb`.
while (my $emb_line = <EMB_OUT>) {
	# looking for "[a]" mark which means an attachment.
	if (
		$emb_line =~ /^(\d+):\s\[a\].*?name=\"(.*)\"/
	) {
		# just print this line and that's it.
		if ($list_mode) {
			print "$emb_line";
			next;
		}
		# grab the index which we'll later use to get
		# an attachment actual content via `emb` again.
		my $idx = $1;
		# save the attachment file name as well.
		my $fname = "$2";
		# if we've specified a particular index(es) of
		# attachments we want to grab and the current one
		# is not one of them - skip it.
		if (@which and not grep /$idx/, @which) {
			next;
		}
		# here, we know this is an attachment we'll save.
		# if our main destination directory hasn't been
		# created yet - do that.
		if (not $att_found) {
			make_path "$dest"
				or die "[ema]: can't create destination dir: $dest.";
		}
		$att_found = 1;
		# now we pass or mail (seats in `$stdin`) into
		# `emb` again but this time with a particular index.
		open2(\*ATT_OUT, \*ATT_IN, "$emb_path", "$idx")
			or die "[ema]: can't open $emb_path.";
		print ATT_IN $stdin;
		close (ATT_IN);
		# prepare a final destination path for our file.
		my $dest_file = "$dest/$fname";
		open(DEST, ">", "$dest_file")
			or die "[ema]: can't open destination file: $dest_file.";
		# and write to the resulting file decoded version of
		# the attachment.
		while (my $att_line = <ATT_OUT>) {
			my $att_line_decoded = decode_base64($att_line);
			print DEST $att_line_decoded;
		}
		close (DEST);
		close (ATT_OUT);
		# print out the destination path for a file.
		print "$dest_file\n";
	}
}
close (EMB_OUT);

# if we haven't find a single attachment we are
# interested in (if we are) - well, just print this error.
if (not $list_mode and not $att_found) {
	die "[ema]: no attachments found.\n";
}
