#! /usr/bin/env python
"""Decode MIME message"""


from mimedecode_version import __version__, __author__, __copyright__, __license__


import sys, os
import email

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


import socket
host_name = socket.gethostname()

me = os.path.basename(sys.argv[0])


def version(exit=1):
    sys.stdout.write("""\
Broytman mimedecode.py version %s, %s
""" % (__version__, __copyright__))
    if exit: sys.exit(0)


def usage(code=0):
    version(0)
    sys.stdout.write("""\
Usage: %s [-h|--help] [-V|--version] [-cCDP] [-f charset] [-d header] [-p header:param] [-beit mask] [filename]
""" % me)
    sys.exit(code)


def output(s, outfile=sys.stdout):
    outfile.write(s)

def output_headers(msg, outfile=sys.stdout):
    unix_from = msg.get_unixfrom()
    if unix_from:
        output(unix_from + os.linesep)
    for key, value in msg.items():
        output("%s: %s\n" % (key, value), outfile)
    output("\n", outfile) # End of headers


def recode(s, charset):
    return unicode(s, charset, "replace").encode(GlobalOptions.default_encoding, "replace")


def recode2(s, charset):
    if charset and charset.lower() <> GlobalOptions.default_encoding:
        s = recode(s, charset)
    return s


def _decode_header(s):
    """Return a decoded string according to RFC 2047.
    NOTE: This is almost the same as email.Utils.decode.
    """
    from types import ListType
    import email.Header

    L = email.Header.decode_header(s)
    if not isinstance(L, ListType):
        # s wasn't decoded
        return s

    rtn = []
    for atom, charset in L:
        if charset is None:
            rtn.append(atom)
        else:
            rtn.append(recode2(atom, charset))
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
    return recode2(s[2], s[0])


def decode_header_param(msg, header, param):
    "Decode mail header's parameter (if exists) and put it back, if it was encoded"

    if msg.has_key(header):
        value = msg.get_param(param, header=header)
        if value:
            from types import TupleType
            if isinstance(value, TupleType):
                new_value = _decode_header_param(value)
            else:
                new_value = _decode_header(value)
            if new_value <> value: # do not bother to touch msg if not changed
                msg.set_param(param, new_value, header)


def decode_headers(msg):
    "Decode message headers according to global options"

    for header in GlobalOptions.decode_headers:
        decode_header(msg, header)

    for header, param in GlobalOptions.decode_header_params:
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
    msg["X-MIME-Autoconverted"] = "from %s to text/plain by %s id %s" % (content_type, host_name, command.split()[0])

    return s


def recode_charset(msg, s):
    "Recode charset of the message to the default charset"

    save_charset = charset = msg.get_content_charset()
    if charset and charset.lower() <> GlobalOptions.default_encoding:
        s = recode2(s, charset)
        content_type = msg.get_content_type()
        set_content_type(msg, content_type, GlobalOptions.default_encoding)
        msg["X-MIME-Autoconverted"] = "from %s to %s by %s id %s" % (save_charset, GlobalOptions.default_encoding, host_name, me)
    return s


def totext(msg, instring):
    "Convert instring content to text"

    if msg.is_multipart(): # Recursively decode all parts of the multipart message
        newfile = StringIO(str(msg))
        newfile.seek(0)
        decode_file(newfile)
        return

    # Decode body and recode charset
    s = decode_body(msg, instring)
    if GlobalOptions.recode_charset:
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
        msg["X-MIME-Autoconverted"] = "from %s to 8bit by %s id %s" % (encoding, host_name, me)

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
        if content_type in GlobalOptions.totext_mask:
            totext(msg, outstring)
            return
        elif content_type in GlobalOptions.binary_mask:
            output_headers(msg)
            output(outstring)
            return
        elif content_type in GlobalOptions.ignore_mask:
            output_headers(msg)
            output("\nMessage body of type `%s' skipped.\n" % content_type)
            return
        elif content_type in GlobalOptions.error_mask:
            raise ValueError, "content type `%s' prohibited" % content_type

    # Neither content type nor masks were listed - decode by default
    totext(msg, outstring)


def decode_file(infile):
    "Decode the entire message"

    msg = email.message_from_file(infile)
    boundary = msg.get_boundary()

    if msg.is_multipart():
        decode_headers(msg)
        output_headers(msg)

        if msg.preamble: # Preserve the first part, it is probably not a RFC822-message
            output(msg.preamble) # Usually it is just a few lines of text (MIME warning)

        for subpart in msg.get_payload():
            output("\n--%s\n" % boundary)
            decode_part(subpart)

        output("\n--%s--\n" % boundary)

        if msg.epilogue:
            output(msg.epilogue)

    else:
        if msg.has_key("Content-Type"): # Simple one-part message - decode it
            decode_part(msg)

        else: # Not a message, just text - copy it literally
            output(str(msg))


class GlobalOptions:
    from m_lib.defenc import default_encoding
    recode_charset = 1 # recode charset of message body

    decode_headers = ["From", "Subject"] # A list of headers to decode
    decode_header_params = [
        ("Content-Type", "name"),
        ("Content-Disposition", "filename"),
    ] # A list of headers' parameters to decode

    totext_mask = [] # A list of content-types to decode
    binary_mask = [] # A list to pass through
    ignore_mask = [] # Ignore (skip, do not decode and do not include into output)
    error_mask = []  # Raise error if encounter one of these


def init():
    from getopt import getopt, GetoptError

    try:
        options, arguments = getopt(sys.argv[1:], 'hVcCDPf:d:p:b:e:i:t:',
            ['help', 'version'])
    except GetoptError:
        usage(1)

    for option, value in options:
        if option == '-h':
            usage()
        elif option == '--help':
            usage()
        elif option == '-V':
            version()
        elif option == '--version':
            version()
        elif option == '-c':
            GlobalOptions.recode_charset = 1
        elif option == '-C':
            GlobalOptions.recode_charset = 0
        elif option == '-f':
            GlobalOptions.default_encoding = value
        elif option == '-d':
            GlobalOptions.decode_headers.append(value)
        elif option == '-D':
            GlobalOptions.decode_headers = []
        elif option == '-p':
            GlobalOptions.decode_header_params.append(value.split(':', 1))
        elif option == '-P':
            GlobalOptions.decode_header_params = []
        elif option == '-t':
            GlobalOptions.totext_mask.append(value)
        elif option == '-b':
            GlobalOptions.binary_mask.append(value)
        elif option == '-i':
            GlobalOptions.ignore_mask.append(value)
        elif option == '-e':
            GlobalOptions.error_mask.append(value)
        else:
            usage(1)

    return arguments


if __name__ == "__main__":
    arguments = init()

    la = len(arguments)
    if la >= 2:
        usage(1)
    if (la == 0) or (arguments[0] == '-'):
        infile = sys.stdin
    else:
        infile = open(arguments[0], 'r')

    decode_file(infile)
