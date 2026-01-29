#!/usr/local/bin/perl

# emb -- email body extractor.
#
# this program has two invoke forms:
#  1 - no arguments specified -- in this case, its behaviour depends
#      on letter structure: if the letter is single-part then it's
#      whole body it printed. in case of multi-part message, it will
#      output content types for each part and their indexes to use
#      with the second invocation form.
#  2 - a body part index (figured out by the means of first invocation
#      form) specified -- in case of multi-part message, it'll print a
#      body part that has a respective index. it doesn't make any sense
#      with single-part message, though it's still valid.


use strict;


# body index we want to examine.
my $which = $ARGV[0];

# first newline (actually, the next line after it) will help us
# to decide what type of message we have: single- or multi-part.
my $expect_boundary_now = 0;

# after we've determined about message type we set it to 1.
my $decision_done = 0;

# the actual decision we've done.
my $multipart = 0;

# used only for multi-part message. in this particular
# program we're interested only in "types" and "body".
my $within = "";

# part boundary for multi-part message.
my $boundary = "";

# we use this two variables for the case where we've
# found the part we're interested in and gonna print it
# up until the next part of end of letter.
my $print_till_next = 0;
my $is_printing = 0;

# current part index.
my $part_idx = 1;

# part types presented in the letter. make use of it only
# for invoking without arguments on multi-part letter.
my @parts = ();

# an indicator that we've already printed a requested
# part and now we're going to just read standard input
# and do nothing with it (it's very important when
# program's called via pipe, so that not to cause deadlocks).
my $discard_stdin = 0;

my $final_output = "";

while (my $line = <STDIN>) {
	# throw stdin away.
	if ($discard_stdin) { next };
	if ($print_till_next and $is_printing) {
		if ($line =~ /--$boundary/) {
			$discard_stdin = 1;
		} else {
			$final_output .= $line;
			next;
		}
	}
	# this basically means we're still in headers.
	if (not $decision_done) {
		# newline has just occured, so examine
		# the maybe-boundary-line.
		if ($expect_boundary_now) {
			# since `emp` processor doesn't leave any explicit
			# information about message boundary (considered overhead)
			# we want to figure out whether or not it is a boundary
			# ourselves. 25 characters would be enough, I think.
			if ( $line =~ /^--(([-=\.A-z\d\\+]){25,})/ ) {
				$boundary = $1;
				$multipart = 1;
				# assume the letter is formatted nice.
				$within = "types";
				$expect_boundary_now = 0;
			} else {
				$multipart = 0;
				# means this line is already part of a body message,
				# so include it in output.
				$final_output .= $line;
			}
			$decision_done = 1;
			next;
		}
		# leave headers, enter the message itself.
		if ($line eq "\n") {
			$expect_boundary_now = 1;
			next;
		}
	}
	if ($decision_done) {
		if ($multipart) {
			if ($within eq "types") {
				# we leave the "types" and enter "body",
				# thus, if we were waiting for the moment to
				# start printing (`$print_till_next`), then
				# it's an appropriate moment for us to do that.
				if ($line eq "\n") {
					$within = "body";
					if ($print_till_next) {
						$is_printing = 1;
					}
					next;
				}
				if ($line =~ /^Content-Type: (.*)/) {
					# if we're looking for a particular type
					# and it is it, the start waiting for an
					# opportunity for us the start printing
					# (not printing actually, but accumulating the output).
					if ($which) {
						if ($which == $part_idx) {
							$print_till_next = 1;
						}
						next;
					}
					# so, it's a multi-part message and we don't want
					# a specific part, then just save the information about
					# part content type.
					else {
						push @parts, $1;
						next;
					}
				}
			}
			if ($within eq "body") {
				# if we're in body and meet the boundary line,
				# the switch back to "types".
				if ($line =~ /^--$boundary/) {
					$within = "types";
					++$part_idx;
					next;
				}
			}
		}
		# if it's a single-part letter, just collect all lines
		# together up to the very end.
		else {
			$final_output .= $line;
		}
	}
}

# if our walk didn't give any results, most likely
# the message index was specified wrong.
if ($which and not $final_output) {
	die "[emb]: wrong body index specified.\n";
}

# if we didn't specify and particular index to obtain
# and just want to look for available parts, then print
# part index (from 1) and type of its content.
if (not $which and $multipart) {
	for my $idx (0 .. $#parts) {
		my $part_type = $parts[$idx];
		my $printed_idx = $idx + 1;
		my $mb_attach_mark = "";
		if ($part_type =~ /; (file)?name=\".*\"/) {
			$mb_attach_mark = "[a] ";
		}
		my $string = "$printed_idx: $mb_attach_mark$part_type\n";
		$final_output .= $string;
	}
}

print $final_output;
