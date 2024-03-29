Name
----

mimedecode -- decode MIME message

Synopsis
--------

mimedecode [ -h|--help ] [ -V|--version ] [ -cCDP ] [ -f charset ]
[ -H|--host=hostname ] [ -d header1[,header2,header3...] ]
[ -d \*[,-header1,-header2,-header3...] ]
[ -p header1[,header2,header3,...]:param1[,param2,param3,...] ]
[ -p \*[,-header1,-header2,-header3,...]:param1[,param2,param3,...] ]
[ -p header1[,header2,header3,...]:\*[,-param1,-param2,-param3,...] ]
[ -p \*[,-header1,-header2,-header3,...]:\*[,-param1,-param2,-param3,...] ]
[ -r header1[,header2,header3...] ] [ -r \*[,-header1,-header2,-header3...] ]
[ -R header1[,header2,header3,...]:param1[,param2,param3,...] ]
[ -R \*[,-header1,-header2,-header3,...]:param1[,param2,param3,...] ]
[ -R header1[,header2,header3,...]:\*[,-param1,-param2,-param3,...] ]
[ -R \*[,-header1,-header2,-header3,...]:\*[,-param1,-param2,-param3,...] ]
[ --set-header header:value ] [ --set-param header:param=value ]
[ -BbeIit mask ] [ --save-headers|body|message mask ] [ -O dest_dir ]
[ -o output_file ] [input_file [output_file] ]

DESCRIPTION
-----------

Mail users, especially in non-English countries, often find that mail
messages arrived in different formats, with different content types, in
different encodings and charsets. Usually it is good because it allows to
use an appropriate format/encoding/whatever. Sometimes, though, some
unification is desirable. For example, one may want to put mail messages
into an archive, make HTML indices, run search indexer, etc. In such
situations converting messages to text in one character set and skipping
some binary attachments is much desirable.

Here is a solution - mimedecode!

This is a program to decode MIME messages. The program expects one input
file (either on command line or on stdin) which is treated as an RFC822
message, and decodes to stdout or an output file. If the file is not an
RFC822 message it is just copied to the output one-to-one. If the file is
a simple RFC822 message it is decoded as one part. If it is a MIME message
with multiple parts ("attachments") all non-multipart subparts are
decoded. Decoding can be controlled by the command-line options.

First, for every part the program removes headers and parameters listed
with -r and -R options. Then, Subject and Content-Disposition headers (and
all headers listed with -d and -p options) are examined. If any of those
exists, they are decoded according to RFC2047. Content-Disposition header
is not decoded (if it was not listed in option -d) - only its "filename"
parameter. Encoded header parameters violate the RFC, but widely deployed
anyway by ignorant coders who never even heard about RFCs. Correct
parameter encoding specified by RFC2231. This program decodes
RFC2231-encoded parameters, too.

Then the body of the message (or the current part) is decoded. Decoding
starts with looking at header Content-Transfer-Encoding. If the header
specifies non-8bit encoding (usually base64 or quoted-printable), the body
is converted to 8bit (can be prevented with -B). Then if its content type
is multipart (multipart/related or multipart/mixed, e.g) every part is
recursively decoded. If it is not multipart, mailcap database is consulted
to find a way to convert the body to plain text (can be prevented with
options -Bbei). (The author has no idea how mailcap can be configured on
OSes other than POSIX, please don't ask; users can consult an example at
https://phdru.name/Software/dotfiles/mailcap.html). The decoding process
uses the first copiousoutput filter it can find. If there are no filters
the body just passed as is.

Then Content-Type header is consulted for charset. If it is not equal to
the current locale charset and recoding is allowed (see options -Cc) the
body text is recoded. Finally message headers and the body are flushed to
stdout.

Please be reminded that in the following options asterisk is a shell
metacharacter and should be escaped or quoted. Either write -d \*,-h1,-h2
or -d '\*,-h1,-h2' or such.

OPTIONS
-------

-h, -help

       Print brief usage help and exit.

-V, --version

       Print version and exit.

-c

       Recode different character sets in message bodies to the current
       default charset; this is the default.

-C

       Do not recode character sets in message bodies.

-f charset

       Force this charset to be used for recoding instead of charset from
       the current locale.

-H hostname, --host=hostname

       Use this hostname in X-MIME-Autoconverted headers instead of the
       current hostname.

-d header1[,header2,header3...]

       Add the header(s) to a list of headers to decode; initially the
       list contains headers "From", "To", "Cc", "Reply-To",
       "Mail-Followup-To" and "Subject".

-d \*[,-header1,-header2,-header3...]

       This variant completely changes headers decoding. First, the list
       of headers to decode is cleared (as with -D). Then all the headers
       are decoded except the given list of exceptions (headers listed
       with '-'). In this mode it would be meaningless to give more than
       one -d options but the program doesn't enforce the limitation.

-D

       Clear the list of headers to decode (make it empty).

-p header1[,header2,header3,...]:param1[,param2,param3,...]

       Add the parameter(s) to a list of headers parameters to decode;
       the parameter(s) will be decoded only for the given header(s).
       Initially the list contains header "Content-Type", parameter
       "name"; and header "Content-Disposition", parameter "filename".

-p \*[,-header1,-header2,-header3,...]:param1[,param2,param3,...]

       Add the parameter(s) to a list of headers parameters to decode;
       the parameter(s) will be decoded for all headers except the given
       ones.

-p header1[,header2,header3,...]:\*[,-param1,-param2,-param3,...]

       Decode all parameters except listed for the given list of headers.

-p \*[,-header1,-header2,-header3,...]:\*[,-param1,-param2,-param3,...]

       Decode all parameters except listed for all headers (except
       listed).

-P

       Clear the list of headers parameters to decode (make it empty).

-r header1[,header2,header3...]

       Add the header(s) to a list of headers to remove completely;
       initially the list is empty.

-r \*[,-header1,-header2,-header3...]

       Remove all headers except listed.

-R header1[,header2,header3,...]:param1[,param2,param3,...]

       Add the parameter(s) to a list of headers parameters to remove;
       the parameter(s) will be removed only for the given header(s).
       Initially the list is empty.

-R \*[,-header1,-header2,-header3,...]:param1[,param2,param3,...]

-R header1[,header2,header3,...]:\*[,-param1,-param2,-param3,...]

-R \*[,-header1,-header2,-header3,...]:\*[,-param1,-param2,-param3,...]

       Remove listed parameters (or all parameters except listed) from
       these headers (or from all headers except listed).

--set-header header:value

       The program sets or changes value for the header to the given
       value (only at the top-level message).

--set-param header:param=value

       The program sets or changes value for the header's parameter to
       the given value (only at the top-level message). The header must
       exist.

-B mask

       Append mask to the list of binary content types that will be not
       content-transfer-decoded (will be left as base64 or such).

-b mask

       Append mask to the list of binary content types; if the message to
       decode has a part of this type the program
       content-transfer-decodes (base64 or whatever to 8bit binary) it
       and outputs the decoded part as is, without any further
       processing.

-e mask

       Append mask to the list of error content types; if the message to
       decode has a part of this type the program fails with ValueError.

-I mask

       Append mask to the list of content types to completely ignore.
       There will be no output - no headers, no body, no warning. For a
       multipart part the entire subtree is removed.

-i mask

       Append mask to the list of content types to ignore; if the message
       to decode has a part of this type the program outputs headers but
       skips the body. Instead a line "Message body of type %s skipped."
       will be issued.

-t mask

       Append mask to the list of content types to convert to text; if
       the message to decode has a part of this type the program consults
       mailcap database, find the first copiousoutput filter and, if any
       filter is found, converts the part.

--save-headers mask

--save-body mask

--save-message mask

       Append mask to lists of content types to save to files;
       --save-headers saves only decoded headers of the message (or the
       current subpart); --save-body saves only decoded body;
       --save-message saves the entire message or subpart (headers +
       body).

-O dest_dir

       Set destination directory for the output files; if the directory
       doesn't exist it will be created. Default is the current
       directory.

-o output_file

       Save output to the file related to the destination directory from
       option -O. Also useful in case of redirected stdin:

mimedecode -o output_file < input_file
cat input_file | mimedecode -o output_file

The 5 list options (-Bbeit) require more explanation. They allow a user to
control body decoding with great flexibility. Think about said mail
archive; for example, its maintainer wants to put there only texts,
convert PDF/Postscript to text, pass HTML and images decoding base64 to
html but leaving images encoded, and ignore everything else. This is how
it could be done:

mimedecode -t application/pdf -t application/postscript -t text/plain -b
text/html -B 'image/\*' -i '\*/\*'

When the program decodes a message (non-MIME or a non-multipart subpart of
a MIME message), it consults Content-Type header. The content type is
searched in all 5 lists, in order "text-binary-ignore-error". If found,
appropriate action is performed. If not found, the program searches the
same lists for "type/\*" mask (the type of "text/html" is just "text"). If
found, appropriate action is performed. If not found, the program searches
the same lists for "\*/\*" mask. If found, appropriate action is performed.
If not found, the program uses the default action, which is to decode
everything to text (if mailcap specifies a filter). This algorithm allows
more specific content types to override less specific: -b image/\* will be
processed earlier than -B \*/\*.

Options -e/-I/-i can also work with multipart subparts of a MIME message.
In case of -I/-i the entire subtree of that multipart is removed; with -i
it's replaced with ignore warning.

Initially all 5 lists are empty, so without any additional parameters the
program always uses the default decoding (as -t \*/\*).

The 3 save options (--save-headers/body/message) are similar. They make
the program to save every non-multipart subpart (only headers, or body, or
the entire subpart: headers + body) that corresponds to the given mask to
a file. Before saving the message (or the subpart) is decoded according to
all other options and is placed to the output stream as usual. Filename
for the file is created using "filename" parameter from the
Content-Disposition header, or "name" parameter from the Content-Type
header if one of those exist; a serial counter is prepended to the
filename to avoid collisions; if there are no name/filename parameters, or
the name/filename parameters contain forbidden characters (null, slash,
backslash) the filename is just the serial counter.

If the file doesn't have any extensions (no dots in the value of the
name/filename parameters, or the name is just the counter) the program
tries to guess an extension by looking up the content type in mime.types
files including .mime.types file in the user's home directory (if it
exists). If the file has an extension the program doesn't try to verify
that it corresponds to the content type.

The file is saved in the directory set with -O (default is the current
directory). The save options are proceeded before -e options so the user
can save the message that causes an error.

ENVIRONMENT
-----------

LANG

LC_ALL

LC_CTYPE

Define current locale settings. Used to determine current default charset
(if your Python is properly installed and configured).

BUGS
----

The program may produce incorrect MIME message. The purpose of the program
is to decode whatever it is possible to decode, not to produce absolutely
correct MIME output. The incorrect parts are obvious - decoded
From/To/Cc/Reply-To/Mail-Followup-To/Subject headers and filenames. Other
than that output is correct MIME message. The program does not try to
guess whether the headers are correct. For example, if a message header
states that charset is iso8859-1, but the body (HTML, for example) is
actually in utf-8 the program will recode the message with the wrong
charset.

AUTHOR
------

Oleg Broytman <phd@phdru.name>

COPYRIGHT
---------

Copyright (C) 2001-2024 PhiloSoft Design.

LICENSE
-------

GNU GPL

NO WARRANTIES
-------------

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

SEE ALSO
--------

mimedecode home page: https://phdru.name/Software/Python/#mimedecode
