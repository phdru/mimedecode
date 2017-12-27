import os
import sys
from . import mimedecode


def version(exit=1):
    sys.stdout.write("""\
Broytman mimedecode.py version %s, %s
""" % (mimedecode.__version__, mimedecode.__copyright__))
    if exit:
        sys.exit(0)


def usage(code=0, errormsg=''):
    version(0)
    sys.stdout.write("""\
Usage: %s [-h|--help] [-V|--version] [-cCDP] [-H|--host=hostname] [-f charset] [-d header1[,h2,...]|*[,-h1,...]] [-p header1[,h2,h3,...]:param1[,p2,p3,...]] [-r header1[,h2,...]|*[,-h1,...]] [-R header1[,h2,h3,...]:param1[,p2,p3,...]] [--set-header header:value] [--set-param header:param=value] [-Bbeit mask] [--save-headers|body|message mask] [-O dest_dir] [-o output_file] [input_file [output_file]]
""" % mimedecode.me)
    if errormsg:
        sys.stderr.write(errormsg + os.linesep)
    sys.exit(code)


class GlobalOptions:
    from m_lib.defenc import default_encoding
    recode_charset = 1  # recode charset of message body

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

    totext_mask = []  # A list of content-types to decode
    binary_mask = []  # A list of content-types to pass through
    # A list of content-types to pass through (content-transfer-decoded).
    decoded_binary_mask = []
    # Ignore (do not decode and do not include into output)
    # but output a warning instead of the body.
    ignore_mask = []
    # Completely ignore - no headers, no body, no warning.
    fully_ignore_mask = []
    error_mask = []  # Raise error if encounter one of these

    save_counter = 0
    save_headers_mask = []
    save_body_mask = []
    save_message_mask = []

    input_filename = None
    output_filename = None
    destination_dir = os.curdir


g = mimedecode.g = GlobalOptions


def get_opts():
    from getopt import getopt, GetoptError

    try:
        options, arguments = getopt(
            sys.argv[1:],
            'hVcCDPH:f:d:p:r:R:b:B:e:I:i:t:O:o:',
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
        elif option == '-I':
            g.fully_ignore_mask.append(value)
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


def main():
    arguments = get_opts()

    la = len(arguments)
    if la == 0:
        g.input_filename = '-'
        infile = sys.stdin
        if g.output_filename:
            outfile = open_output_file(g.output_filename)
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
                outfile = open_output_file(g.output_filename)
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
                outfile = open_output_file(g.output_filename)
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
    if hasattr(outfile, 'buffer'):
        def output_bytes(s):
            if not isinstance(s, bytes):
                s = s.encode(g.default_encoding, "replace")
            outfile.buffer.write(s)
        output = output_bytes
    else:
        output = outfile.write
    mimedecode.output = output

    import email
    msg = email.message_from_file(infile)

    for header, value in g.set_header_value:
        mimedecode.set_header(msg, header, value)

    for header, param, value in g.set_header_param:
        if header in msg:
            msg.set_param(param, value, header)

    try:
        mimedecode.decode_message(msg)
    finally:
        infile.close()
        outfile.close()


if __name__ == "__main__":
    main()
