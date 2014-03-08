#! /usr/bin/env python
"""Decode MIME message"""

from mimedecode_version import __version__, __author__, __copyright__, __license__

import sys, os
import email

me = os.path.basename(sys.argv[0])


def version(exit=1):
    sys.stdout.write("""\
Broytman mimedecode.py version %s, %s
""" % (__version__, __copyright__))
    if exit: sys.exit(0)

def usage(code=0, errormsg=''):
    version(0)
    sys.stdout.write("""\
Usage: %s [-h|--help] [-V|--version] [-cCDP] [-H|--host=hostname] [-f charset] [-d header1[,h2,...]|*[,-h1,...]] [-p header1[,h2,h3,...]:param1[,p2,p3,...]] [-r header] [-R header:param] [--remove-params=header] [-beit mask] [-o output_file] [input_file [output_file]]
""" % me)
    if errormsg:
        sys.stderr.write(errormsg + '\n')
    sys.exit(code)


def output_headers(msg):
    unix_from = msg.get_unixfrom()
    if unix_from:
        output(unix_from + '\n')
    for key, value in msg.items():
        output("%s: %s\n" % (key, value))
    output("\n") # End of headers


def recode(s, charset):
    return unicode(s, charset, "replace").encode(gopts.default_encoding, "replace")

def recode_if_needed(s, charset):
    if charset and charset.lower() <> gopts.default_encoding:
        s = recode(s, charset)
    return s


def _decode_header(s):
    """Return a decoded string according to RFC 2047.
    NOTE: This is almost the same as email.Utils.decode.
    """
    import email.Header

    L = email.Header.decode_header(s)
    if not isinstance(L, list):
        # s wasn't decoded
        return s

    rtn = []
    for atom, charset in L:
        if charset is None:
            rtn.append(atom)
        else:
            rtn.append(recode_if_needed(atom, charset))
        rtn.append(' ')
    del rtn[-1] # remove the last space

    # Now that we've decoded everything, we just need to join all the parts
    # together into the final string.
    return ''.join(rtn)

def decode_header(msg, header):
    "Decode mail header (if exists) and put it back, if it was encoded"

    if msg.has_key(header):
        value = msg[header]
        new_value = _decode_header(value)
        if new_value <> value: # do not bother to touch msg if not changed
            set_header(msg, header, new_value)


def _decode_header_param(s):
    return recode_if_needed(s[2], s[0])

def decode_header_param(msg, header, param):
    "Decode mail header's parameter (if exists) and put it back, if it was encoded"

    if msg.has_key(header):
        value = msg.get_param(param, header=header)
        if value:
            if isinstance(value, tuple):
                new_value = _decode_header_param(value)
            else:
                new_value = _decode_header(value)
            if new_value <> value: # do not bother to touch msg if not changed
                msg.set_param(param, new_value, header)


def _get_exceptions(list):
    return [x[1:].lower() for x in list[1:] if x[0]=='-']

def decode_headers(msg):
    "Decode message headers according to global options"

    for header in gopts.remove_headers:
        del msg[header]

    for header in gopts.remove_all_params:
        value = msg[header]
        if value is None: # No such header
            continue
        if ';' not in value: # There are no parameters
            continue
        del msg[header] # Delete all such headers
        # Get the value without parameters and set it back
        msg[header] = value.split(';')[0].strip()

    for header, param in gopts.remove_header_params:
        msg.del_param(param, header)

    for header_list in gopts.decode_headers:
        header_list = header_list.split(',')
        if header_list[0] == '*': # Decode all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    decode_header(msg, header)
        else: # Decode listed headers
            for header in header_list:
                decode_header(msg, header)

    for header_list, param_list in gopts.decode_header_params:
        header_list = header_list.split(',')
        param_list = param_list.split(',')
        if header_list[0] == '*': # Decode for all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    for param in param_list:
                        decode_header_param(msg, header, param)
        else: # Decode for listed headers
            for header in header_list:
                for param in param_list:
                    decode_header_param(msg, header, param)


def set_header(msg, header, value):
    "Replace header"

    if msg.has_key(header):
        msg.replace_header(header, value)
    else:
        msg[header] = value


def set_content_type(msg, newtype, charset=None):
    msg.set_type(newtype)

    if charset:
        msg.set_param("charset", charset, "Content-Type")


caps = None # Globally stored mailcap database; initialized only if needed

def decode_body(msg, s):
    "Decode body to plain text using first copiousoutput filter from mailcap"

    import mailcap, tempfile

    global caps
    if caps is None:
        caps = mailcap.getcaps()

    content_type = msg.get_content_type()
    filename = tempfile.mktemp()
    command = None

    entries = mailcap.lookup(caps, content_type, "view")
    for entry in entries:
        if entry.has_key('copiousoutput'):
            if entry.has_key('test'):
                test = mailcap.subst(entry['test'], content_type, filename)
                if test and os.system(test) != 0:
                    continue
            command = mailcap.subst(entry["view"], content_type, filename)
            break

    if not command:
        return s

    file = open(filename, 'w')
    file.write(s)
    file.close()

    pipe = os.popen(command, 'r')
    s = pipe.read()
    pipe.close()
    os.remove(filename)

    set_content_type(msg, "text/plain")
    msg["X-MIME-Autoconverted"] = "from %s to text/plain by %s id %s" % (content_type, gopts.host_name, command.split()[0])

    return s


def recode_charset(msg, s):
    "Recode charset of the message to the default charset"

    save_charset = charset = msg.get_content_charset()
    if charset and charset.lower() <> gopts.default_encoding:
        s = recode_if_needed(s, charset)
        content_type = msg.get_content_type()
        set_content_type(msg, content_type, gopts.default_encoding)
        msg["X-MIME-Autoconverted"] = "from %s to %s by %s id %s" % (save_charset, gopts.default_encoding, gopts.host_name, me)
    return s


def totext(msg, instring):
    "Convert instring content to text"

    # Decode body and recode charset
    s = decode_body(msg, instring)
    if gopts.recode_charset:
        s = recode_charset(msg, s)

    output_headers(msg)
    output(s)


def decode_part(msg):
    "Decode one part of the message"

    decode_headers(msg)
    encoding = msg["Content-Transfer-Encoding"]

    if encoding in (None, '', '7bit', '8bit', 'binary'):
        outstring = str(msg.get_payload())
    else: # Decode from transfer ecoding to text or binary form
        outstring = str(msg.get_payload(decode=1))
        set_header(msg, "Content-Transfer-Encoding", "8bit")
        msg["X-MIME-Autoconverted"] = "from %s to 8bit by %s id %s" % (encoding, gopts.host_name, me)

    # Test all mask lists and find what to do with this content type
    masks = []
    ctype = msg.get_content_type()
    if ctype:
        masks.append(ctype)
    mtype = msg.get_content_maintype()
    if mtype:
        masks.append(mtype + '/*')
    masks.append('*/*')

    for content_type in masks:
        if content_type in gopts.totext_mask:
            totext(msg, outstring)
            return
        elif content_type in gopts.binary_mask:
            output_headers(msg)
            output(outstring)
            return
        elif content_type in gopts.ignore_mask:
            output_headers(msg)
            output("\nMessage body of type `%s' skipped.\n" % content_type)
            return
        elif content_type in gopts.error_mask:
            raise ValueError, "content type `%s' prohibited" % content_type

    # Neither content type nor masks were listed - decode by default
    totext(msg, outstring)


def decode_multipart(msg):
    "Decode multipart"

    decode_headers(msg)
    output_headers(msg)

    if msg.preamble: # Preserve the first part, it is probably not a RFC822-message
        output(msg.preamble) # Usually it is just a few lines of text (MIME warning)

    boundary = msg.get_boundary()

    for subpart in msg.get_payload():
        if boundary:
            output("\n--%s\n" % boundary)

        # Recursively decode all parts of the subpart
        decode_message(subpart)

    if boundary:
        output("\n--%s--\n" % boundary)

    if msg.epilogue:
        output(msg.epilogue)


def decode_message(msg):
    "Decode message"

    if msg.is_multipart():
        decode_multipart(msg)
    elif len(msg): # Simple one-part message (there are headers) - decode it
        decode_part(msg)
    else: # Not a message, just text - copy it literally
        output(msg.as_string())


class GlobalOptions:
    from m_lib.defenc import default_encoding
    recode_charset = 1 # recode charset of message body

    host_name = None

    # A list of headers to decode
    decode_headers = ["From", "To", "Cc", "Reply-To", "Mail-Followup-To",
                      "Subject"]

    # A list of headers parameters to decode
    decode_header_params = [
        ("Content-Type", "name"),
        ("Content-Disposition", "filename"),
    ]

    # A list of headers to remove
    remove_headers = []
    # A list of headers parameters to remove
    remove_header_params = []
    # A list of headers to be stripped of all parameters
    remove_all_params = []

    totext_mask = [] # A list of content-types to decode
    binary_mask = [] # A list to pass through
    ignore_mask = [] # Ignore (skip, do not decode and do not include into output)
    error_mask = []  # Raise error if encounter one of these

    input_filename = None
    output_filename = None

gopts = GlobalOptions


def get_opt():
    from getopt import getopt, GetoptError

    try:
        options, arguments = getopt(sys.argv[1:],
            'hVcCDPH:f:d:p:r:R:b:e:i:t:o:',
            ['help', 'version', 'host=', 'remove-params='])
    except GetoptError:
        usage(1)

    for option, value in options:
        if option in ('-h', '--help'):
            usage()
        elif option in ('-V', '--version'):
            version()
        elif option == '-c':
            gopts.recode_charset = 1
        elif option == '-C':
            gopts.recode_charset = 0
        elif option in ('-H', '--host'):
            gopts.host_name = value
        elif option == '-f':
            gopts.default_encoding = value
        elif option == '-d':
            if value.startswith('*'):
                gopts.decode_headers = []
            gopts.decode_headers.append(value)
        elif option == '-D':
            gopts.decode_headers = []
        elif option == '-p':
            gopts.decode_header_params.append(value.split(':', 1))
        elif option == '-P':
            gopts.decode_header_params = []
        elif option == '-r':
            gopts.remove_headers.append(value)
        elif option == '-R':
            gopts.remove_header_params.append(value.split(':', 1))
        elif option == '--remove-params':
            gopts.remove_all_params.append(value)
        elif option == '-t':
            gopts.totext_mask.append(value)
        elif option == '-b':
            gopts.binary_mask.append(value)
        elif option == '-i':
            gopts.ignore_mask.append(value)
        elif option == '-e':
            gopts.error_mask.append(value)
        elif option == '-o':
            gopts.output_filename = value
        else:
            usage(1)

    return arguments


if __name__ == "__main__":
    arguments = get_opt()

    la = len(arguments)
    if la == 0:
        gopts.input_filename = '-'
        infile = sys.stdin
        if gopts.output_filename:
            outfile = open(gopts.output_filename, 'w')
        else:
            gopts.output_filename = '-'
            outfile = sys.stdout
    elif la in (1, 2):
        if (arguments[0] == '-'):
            gopts.input_filename = '-'
            infile = sys.stdin
        else:
            gopts.input_filename = arguments[0]
            infile = open(arguments[0], 'r')
        if la == 1:
            if gopts.output_filename:
                outfile = open(gopts.output_filename, 'w')
            else:
                gopts.output_filename = '-'
                outfile = sys.stdout
        elif la == 2:
            if gopts.output_filename:
                usage(1, 'Too many output filenames')
            if (arguments[1] == '-'):
                gopts.output_filename = '-'
                outfile = sys.stdout
            else:
                gopts.output_filename = arguments[1]
                outfile = open(arguments[1], 'w')
    else:
        usage(1, 'Too many arguments')

    if (infile is sys.stdin) and sys.stdin.isatty():
        if (outfile is sys.stdout) and sys.stdout.isatty():
            usage()
        usage(1, 'Filtering from console is forbidden')

    if not gopts.host_name:
        import socket
        gopts.host_name = socket.gethostname()

    gopts.outfile = outfile
    output = outfile.write

    try:
        decode_message(email.message_from_file(infile))
    finally:
        infile.close()
        outfile.close()
