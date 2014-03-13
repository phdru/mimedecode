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
        Usage: %s [-h|--help] [-V|--version] [-cCDP] [-H|--host=hostname] [-f charset] [-d header1[,h2,...]|*[,-h1,...]] [-p header1[,h2,h3,...]:param1[,p2,p3,...]] [-r header1[,h2,...]|*[,-h1,...]] [-R header1[,h2,h3,...]:param1[,p2,p3,...]] [--set-header header:value] [--set-param header:param=value] [-Bbeit mask] [--save-headers|body|message mask] [-O dest_dir] [-o output_file] [input_file [output_file]]
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


def recode_if_needed(s, charset):
    if charset and charset.lower() <> g.default_encoding:
        s = unicode(s, charset, "replace").encode(g.default_encoding, "replace")
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

def _decode_headers_params(msg, header, decode_all_params, param_list):
    if decode_all_params:
        params = msg.get_params(header=header)
        if params:
            for param, value in params:
                if param not in param_list:
                    decode_header_param(msg, header, param)
    else:
        for param in param_list:
            decode_header_param(msg, header, param)

def _remove_headers_params(msg, header, remove_all_params, param_list):
    if remove_all_params:
        params = msg.get_params(header=header)
        if params:
            if param_list:
                for param, value in params:
                    if param not in param_list:
                        msg.del_param(param, header)
            else:
                value = msg[header]
                if value is None: # No such header
                    return
                if ';' not in value: # There are no parameters
                    return
                del msg[header] # Delete all such headers
                # Get the value without parameters and set it back
                msg[header] = value.split(';')[0].strip()
    else:
        for param in param_list:
            msg.del_param(param, header)

def decode_headers(msg):
    "Decode message headers according to global options"

    for header_list in g.remove_headers:
        header_list = header_list.split(',')
        if header_list[0] == '*': # Remove all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    del msg[header]
        else: # Remove listed headers
            for header in header_list:
                del msg[header]

    for header_list, param_list in g.remove_headers_params:
        header_list = header_list.split(',')
        param_list = param_list.split(',')
        remove_all_params = param_list[0] == '*' # Remove all params except listed
        if remove_all_params:
            param_list = _get_exceptions(param_list)
        if header_list[0] == '*': # Remove for all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    _remove_headers_params(msg, header, remove_all_params, param_list)
        else: # Decode for listed headers
            for header in header_list:
                _remove_headers_params(msg, header, remove_all_params, param_list)

    for header_list in g.decode_headers:
        header_list = header_list.split(',')
        if header_list[0] == '*': # Decode all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    decode_header(msg, header)
        else: # Decode listed headers
            for header in header_list:
                decode_header(msg, header)

    for header_list, param_list in g.decode_header_params:
        header_list = header_list.split(',')
        param_list = param_list.split(',')
        decode_all_params = param_list[0] == '*' # Decode all params except listed
        if decode_all_params:
            param_list = _get_exceptions(param_list)
        if header_list[0] == '*': # Decode for all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    _decode_headers_params(msg, header, decode_all_params, param_list)
        else: # Decode for listed headers
            for header in header_list:
                _decode_headers_params(msg, header, decode_all_params, param_list)


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
    msg["X-MIME-Autoconverted"] = "from %s to text/plain by %s id %s" % (content_type, g.host_name, command.split()[0])

    return s


def recode_charset(msg, s):
    "Recode charset of the message to the default charset"

    save_charset = charset = msg.get_content_charset()
    if charset and charset.lower() <> g.default_encoding:
        s = recode_if_needed(s, charset)
        content_type = msg.get_content_type()
        set_content_type(msg, content_type, g.default_encoding)
        msg["X-MIME-Autoconverted"] = "from %s to %s by %s id %s" % (save_charset, g.default_encoding, g.host_name, me)
    return s


def totext(msg, instring):
    "Convert instring content to text"

    # Decode body and recode charset
    s = decode_body(msg, instring)
    if g.recode_charset:
        s = recode_charset(msg, s)

    output_headers(msg)
    output(s)
    return s


def _save_message(msg, outstring, save_headers=False, save_body=False):
    for header, param in (
        ("Content-Disposition", "filename"),
        ("Content-Type", "name"),
    ):
        fname = msg.get_param(param, header=header)
        if fname:
            fname = '-' + fname
            break
    else:
        fname = ''
    g.save_counter += 1
    fname = str(g.save_counter) + fname

    global output
    save_output = output
    outfile = open(os.path.join(g.destination_dir, fname), 'w')
    output = outfile.write
    if save_headers:
        output_headers(msg)
    if save_body:
        output(outstring)
    outfile.close()
    output = save_output


def decode_part(msg):
    "Decode one part of the message"

    decode_headers(msg)

    # Test all mask lists and find what to do with this content type
    masks = []
    ctype = msg.get_content_type()
    if ctype:
        masks.append(ctype)
    mtype = msg.get_content_maintype()
    if mtype:
        masks.append(mtype + '/*')
    masks.append('*/*')

    left_binary = False
    for content_type in masks:
        if content_type in g.totext_mask or \
           content_type in g.decoded_binary_mask:
            break
        elif content_type in g.binary_mask:
            left_binary = True
            break

    encoding = msg["Content-Transfer-Encoding"]
    if left_binary or encoding in (None, '', '7bit', '8bit', 'binary'):
        outstring = msg.get_payload()
    else: # Decode from transfer ecoding to text or binary form
        outstring = msg.get_payload(decode=1)
        set_header(msg, "Content-Transfer-Encoding", "8bit")
        msg["X-MIME-Autoconverted"] = "from %s to 8bit by %s id %s" % (encoding, g.host_name, me)

    for content_type in masks:
        if content_type in g.totext_mask:
            outstring = totext(msg, outstring)
            break
        elif content_type in g.binary_mask or \
             content_type in g.decoded_binary_mask:
            output_headers(msg)
            output(outstring)
            break
        elif content_type in g.ignore_mask:
            output_headers(msg)
            output("\nMessage body of type %s skipped.\n" % ctype)
            break
        elif content_type in g.error_mask:
            break
    else:
        # Neither content type nor masks were listed - decode by default
        outstring = totext(msg, outstring)

    for content_type in masks:
        if content_type in g.save_headers_mask:
            _save_message(msg, outstring, save_headers=True, save_body=False)
        elif content_type in g.save_body_mask:
            _save_message(msg, outstring, save_headers=False, save_body=True)
        elif content_type in g.save_message_mask:
            _save_message(msg, outstring, save_headers=True, save_body=True)

    for content_type in masks:
        if content_type in g.error_mask:
            raise ValueError, "content type %s prohibited" % ctype

def decode_multipart(msg):
    "Decode multipart"

    decode_headers(msg)
    output_headers(msg)

    if msg.preamble: # Preserve the first part, it is probably not a RFC822-message
        output(msg.preamble) # Usually it is just a few lines of text (MIME warning)
    if msg.preamble is not None:
        output("\n")

    first_subpart = True
    boundary = msg.get_boundary()

    for subpart in msg.get_payload():
        if boundary:
            if first_subpart:
                first_subpart = False
            else:
                output("\n")
            output("--%s\n" % boundary)

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
    remove_headers_params = []

    # A list of header/value pairs to set
    set_header_value = []
    # A list of header/parameter/value triples to set
    set_header_param = []

    totext_mask = [] # A list of content-types to decode
    binary_mask = [] # A list of content-types to pass through
    decoded_binary_mask = [] # A list of content-types to pass through (content-transfer-decoded)
    ignore_mask = [] # Ignore (skip, do not decode and do not include into output)
    error_mask = []  # Raise error if encounter one of these

    save_counter = 0
    save_headers_mask = []
    save_body_mask = []
    save_message_mask = []

    input_filename = None
    output_filename = None
    destination_dir = os.curdir

g = GlobalOptions


def get_opts():
    from getopt import getopt, GetoptError

    try:
        options, arguments = getopt(sys.argv[1:],
            'hVcCDPH:f:d:p:r:R:b:B:e:i:t:O:o:',
            ['help', 'version', 'host=',
             'save-headers=', 'save-body=', 'save-message=',
             'set-header=', 'set-param='])
    except GetoptError:
        usage(1)

    for option, value in options:
        if option in ('-h', '--help'):
            usage()
        elif option in ('-V', '--version'):
            version()
        elif option == '-c':
            g.recode_charset = 1
        elif option == '-C':
            g.recode_charset = 0
        elif option in ('-H', '--host'):
            g.host_name = value
        elif option == '-f':
            g.default_encoding = value
        elif option == '-d':
            if value.startswith('*'):
                g.decode_headers = []
            g.decode_headers.append(value)
        elif option == '-D':
            g.decode_headers = []
        elif option == '-p':
            g.decode_header_params.append(value.split(':', 1))
        elif option == '-P':
            g.decode_header_params = []
        elif option == '-r':
            g.remove_headers.append(value)
        elif option == '-R':
            g.remove_headers_params.append(value.split(':', 1))
        elif option == '--set-header':
            g.set_header_value.append(value.split(':', 1))
        elif option == '--set-param':
            header, value = value.split(':', 1)
            if '=' in value:
                param, value = value.split('=', 1)
            else:
                param, value = value.split(':', 1)
            g.set_header_param.append((header, param, value))
        elif option == '-t':
            g.totext_mask.append(value)
        elif option == '-B':
            g.binary_mask.append(value)
        elif option == '-b':
            g.decoded_binary_mask.append(value)
        elif option == '-i':
            g.ignore_mask.append(value)
        elif option == '-e':
            g.error_mask.append(value)
        elif option == '--save-headers':
            g.save_headers_mask.append(value)
        elif option == '--save-body':
            g.save_body_mask.append(value)
        elif option == '--save-message':
            g.save_message_mask.append(value)
        elif option == '-O':
            g.destination_dir = value
        elif option == '-o':
            g.output_filename = value
        else:
            usage(1)

    return arguments


if __name__ == "__main__":
    arguments = get_opts()

    la = len(arguments)
    if la == 0:
        g.input_filename = '-'
        infile = sys.stdin
        if g.output_filename:
            outfile = open(os.path.join(g.destination_dir, g.output_filename), 'w')
        else:
            g.output_filename = '-'
            outfile = sys.stdout
    elif la in (1, 2):
        if (arguments[0] == '-'):
            g.input_filename = '-'
            infile = sys.stdin
        else:
            g.input_filename = arguments[0]
            infile = open(arguments[0], 'r')
        if la == 1:
            if g.output_filename:
                outfile = open(os.path.join(g.destination_dir, g.output_filename), 'w')
            else:
                g.output_filename = '-'
                outfile = sys.stdout
        elif la == 2:
            if g.output_filename:
                usage(1, 'Too many output filenames')
            if (arguments[1] == '-'):
                g.output_filename = '-'
                outfile = sys.stdout
            else:
                g.output_filename = arguments[1]
                outfile = open(os.path.join(g.destination_dir, g.output_filename), 'w')
    else:
        usage(1, 'Too many arguments')

    if (infile is sys.stdin) and sys.stdin.isatty():
        if (outfile is sys.stdout) and sys.stdout.isatty():
            usage()
        usage(1, 'Filtering from console is forbidden')

    if not g.host_name:
        import socket
        g.host_name = socket.gethostname()

    g.outfile = outfile
    output = outfile.write

    msg = email.message_from_file(infile)

    for header, value in g.set_header_value:
        msg[header] = value

    for header, param, value in g.set_header_param:
        if header in msg:
            msg.set_param(param, value, header)

    try:
        decode_message(msg)
    finally:
        infile.close()
        outfile.close()
