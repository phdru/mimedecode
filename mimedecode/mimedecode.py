"""Decode MIME message"""

import os
import shutil
import subprocess
import sys

from .__version__ import __version__, __copyright__

if sys.version_info[0] >= 3:
    # Replace email.message._formatparam with _formatparam from Python 2.7
    # to avoid re-encoding non-ascii params.
    from mimedecode import formatparam_27  # noqa: F401: Imported for its side effect

me = os.path.basename(sys.argv[0])


def output_headers(msg):
    unix_from = msg.get_unixfrom()
    if unix_from:
        output(unix_from)
        output(os.linesep)
    for key, value in msg.items():
        output(key)
        output(": ")
        value = value.split(';', 1)
        output(value[0])
        if len(value) == 2:
            output(";")
            output(_decode_header(value[1], strip=False))
        output(os.linesep)
    output(os.linesep)  # End of headers


def recode_if_needed(s, charset):
    if bytes is str:  # Python2
        if isinstance(s, bytes) and \
                charset and charset.lower() != g.default_encoding:
            s = s.decode(charset, "replace").\
                encode(g.default_encoding, "replace")
    else:  # Python3
        if isinstance(s, bytes):
            s = s.decode(charset, "replace")
    return s


def _decode_header(s, strip=True):
    """Return a decoded string according to RFC 2047.
    NOTE: This is almost the same as email.Utils.decode.
    """
    import email.header

    L = email.header.decode_header(s)
    if not isinstance(L, list):
        # s wasn't decoded
        return s

    rtn = []
    for atom, charset in L:
        atom = recode_if_needed(atom, charset or g.default_encoding)
        if strip:
            atom = atom.strip()
        rtn.append(atom)

    # Now that we've decoded everything, we just need to join all the parts
    # together into the final string.
    return ' '.join(rtn)


def decode_header(msg, header):
    "Decode mail header (if exists) and put it back, if it was encoded"

    if header in msg:
        value = msg[header]
        new_value = _decode_header(value)
        if new_value != value:  # do not bother to touch msg if not changed
            set_header(msg, header, new_value)


def decode_header_param(msg, header, param):
    """Decode mail header's parameter

    Decode mail header's parameter (if exists)
    and put it back if it was encoded.
    """
    if header in msg:
        value = msg.get_param(param, header=header)
        if value:
            if isinstance(value, tuple):
                new_value = recode_if_needed(value[2], value[0])
            else:
                new_value = _decode_header(value)
            if new_value != value:  # do not bother to touch msg if not changed
                msg.set_param(param, new_value, header)


def _get_exceptions(list):
    return [x[1:].lower() for x in list[1:] if x[0] == '-']


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
                if value is None:  # No such header
                    return
                if ';' not in value:  # There are no parameters
                    return
                del msg[header]  # Delete all such headers
                # Get the value without parameters and set it back
                msg[header] = value.split(';')[0].strip()
    else:
        for param in param_list:
            msg.del_param(param, header)


def decode_headers(msg):
    "Decode message headers according to global options"

    for header_list in g.remove_headers:
        header_list = header_list.split(',')
        if header_list[0] == '*':  # Remove all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    del msg[header]
        else:  # Remove listed headers
            for header in header_list:
                del msg[header]

    for header_list, param_list in g.remove_headers_params:
        header_list = header_list.split(',')
        param_list = param_list.split(',')
        # Remove all params except listed.
        remove_all_params = param_list[0] == '*'
        if remove_all_params:
            param_list = _get_exceptions(param_list)
        if header_list[0] == '*':  # Remove for all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    _remove_headers_params(
                        msg, header, remove_all_params, param_list)
        else:  # Decode for listed headers
            for header in header_list:
                _remove_headers_params(
                    msg, header, remove_all_params, param_list)

    for header_list in g.decode_headers:
        header_list = header_list.split(',')
        if header_list[0] == '*':  # Decode all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    decode_header(msg, header)
        else:  # Decode listed headers
            for header in header_list:
                decode_header(msg, header)

    for header_list, param_list in g.decode_header_params:
        header_list = header_list.split(',')
        param_list = param_list.split(',')
        # Decode all params except listed.
        decode_all_params = param_list[0] == '*'
        if decode_all_params:
            param_list = _get_exceptions(param_list)
        if header_list[0] == '*':  # Decode for all headers except listed
            header_list = _get_exceptions(header_list)
            for header in msg.keys():
                if header.lower() not in header_list:
                    _decode_headers_params(
                        msg, header, decode_all_params, param_list)
        else:  # Decode for listed headers
            for header in header_list:
                _decode_headers_params(
                    msg, header, decode_all_params, param_list)


def set_header(msg, header, value):
    "Replace header"

    if header in msg:
        msg.replace_header(header, value)
    else:
        msg[header] = value


def set_content_type(msg, newtype, charset=None):
    msg.set_type(newtype)

    if charset:
        msg.set_param("charset", charset, "Content-Type")


caps = None  # Globally stored mailcap database; initialized only if needed


def decode_body(msg, s):
    "Decode body to plain text using first copiousoutput filter from mailcap"

    try:
        import mailcap
    except ImportError:  # Python 3.13
        from mimedecode import mailcap_312 as mailcap
    import tempfile

    global caps
    if caps is None:
        caps = mailcap.getcaps()

    content_type = msg.get_content_type()
    if content_type.startswith('text/'):
        charset = msg.get_content_charset()
    else:
        charset = None
    tmpfile = tempfile.NamedTemporaryFile()
    command = None

    entries = mailcap.lookup(caps, content_type, "view")
    for entry in entries:
        if 'copiousoutput' in entry:
            if 'test' in entry:
                test = mailcap.subst(entry['test'], content_type, tmpfile.name)
                if test and os.system(test) != 0:
                    continue
            command = mailcap.subst(entry["view"], content_type, tmpfile.name)
            break

    if not command:
        return s

    if charset and bytes is not str and isinstance(s, bytes):  # Python3
        s = s.decode(charset, "replace")
    if not isinstance(s, bytes):
        s = s.encode(g.default_encoding, "replace")
    tmpfile.write(s)
    tmpfile.flush()

    pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    new_s = pipe.stdout.read()
    pipe.stdout.close()
    if pipe.wait() == 0:  # result=0, Ok
        s = new_s
        if bytes is not str and isinstance(s, bytes):  # Python3
            s = s.decode(g.default_encoding, "replace")
        if charset and not isinstance(s, bytes):
            s = s.encode(charset, "replace")
        set_content_type(msg, "text/plain")
        msg["X-MIME-Autoconverted"] = \
            "from %s to text/plain by %s id %s" \
            % (content_type, g.host_name, command.split()[0])
    else:
        msg["X-MIME-Autoconverted"] = \
            "failed conversion from %s to text/plain by %s id %s" \
            % (content_type, g.host_name, command.split()[0])
    tmpfile.close()  # Will be removed on close

    return s


def recode_charset(msg, s):
    "Recode charset of the message to the default charset"

    save_charset = charset = msg.get_content_charset()
    if charset and charset.lower() != g.default_encoding:
        s = recode_if_needed(s, charset)
        content_type = msg.get_content_type()
        set_content_type(msg, content_type, g.default_encoding)
        msg["X-MIME-Autoconverted"] = \
            "from %s to %s by %s id %s" \
            % (save_charset, g.default_encoding, g.host_name, me)
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


mimetypes = None


def _guess_extension(ctype):
    global mimetypes
    if mimetypes is None:
        import mimetypes
        mimetypes.init()
        user_mime_type = os.path.expanduser('~/.mime.types')
        if os.path.exists(user_mime_type):
            mimetypes._db.read(user_mime_type)
    return mimetypes.guess_extension(ctype)


def _save_message(msg, outstring, save_headers=False, save_body=False):
    for header, param in (
        ("Content-Disposition", "filename"),
        ("Content-Type", "name"),
    ):
        fname = msg.get_param(param, header=header)
        if fname:
            if isinstance(fname, tuple):
                fname = fname[2]  # Do not recode if it isn't recoded yet
            try:
                    for forbidden in chr(0), '/', '\\':
                        if forbidden in fname:
                            raise ValueError
            except ValueError:
                continue
            fname = '-' + fname
            break
    else:
        fname = ''
    g.save_counter += 1
    fname = str(g.save_counter) + fname
    if '.' not in fname:
        ext = _guess_extension(msg.get_content_type())
        if ext:
            fname += ext

    global output
    save_output = output
    outfile = open_output_file(fname)

    def _output_bytes(s):
        if not isinstance(s, bytes):
            s = s.encode(g.default_encoding, "replace")
        outfile.write(s)

    output = _output_bytes
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
        mtype = ctype.split('/')[0]
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
        elif content_type in g.fully_ignore_mask:
            return

    encoding = msg["Content-Transfer-Encoding"]
    if left_binary or encoding in (None, '', '7bit', '8bit', 'binary'):
        outstring = msg.get_payload()
    else:  # Decode from transfer ecoding to text or binary form
        outstring = msg.get_payload(decode=1)
        set_header(msg, "Content-Transfer-Encoding", "8bit")
        msg["X-MIME-Autoconverted"] = \
            "from %s to 8bit by %s id %s" % (encoding, g.host_name, me)

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
            output("%sMessage body of type %s skipped.%s"
                   % (os.linesep, ctype, os.linesep))
            break
        elif content_type in g.error_mask:
            break
    else:
        # Neither content type nor masks were listed - decode by default
        outstring = totext(msg, outstring)

    for content_type in masks:
        if content_type in g.save_headers_mask:
            _save_message(msg, outstring, save_headers=True, save_body=False)
        if content_type in g.save_body_mask:
            _save_message(msg, outstring, save_headers=False, save_body=True)
        if content_type in g.save_message_mask:
            _save_message(msg, outstring, save_headers=True, save_body=True)

    for content_type in masks:
        if content_type in g.error_mask:
            raise ValueError("content type %s prohibited" % ctype)


def decode_multipart(msg):
    "Decode multipart"

    decode_headers(msg)
    boundary = msg.get_boundary()

    masks = []
    ctype = msg.get_content_type()
    if ctype:
        masks.append(ctype)
        mtype = ctype.split('/')[0]
        masks.append(mtype + '/*')
    masks.append('*/*')

    for content_type in masks:
        if content_type in g.fully_ignore_mask:
            return
        elif content_type in g.ignore_mask:
            output_headers(msg)
            output("%sMessage body of type %s skipped.%s"
                   % (os.linesep, ctype, os.linesep))
            if boundary:
                output("%s--%s--%s" % (os.linesep, boundary, os.linesep))
            return

    for content_type in masks:
        if content_type in g.save_body_mask or \
                content_type in g.save_message_mask:
            _out_l = []
            first_subpart = True
            for subpart in msg.get_payload():
                if first_subpart:
                    first_subpart = False
                else:
                    _out_l.append(os.linesep)
                _out_l.append("--%s%s" % (boundary, os.linesep))
                _out_l.append(subpart.as_string())
            _out_l.append("%s--%s--%s" % (os.linesep, boundary, os.linesep))
            outstring = ''.join(_out_l)
            break
    else:
        outstring = None

    for content_type in masks:
        if content_type in g.save_headers_mask:
            _save_message(msg, outstring, save_headers=True, save_body=False)
        if content_type in g.save_body_mask:
            _save_message(msg, outstring, save_headers=False, save_body=True)
        if content_type in g.save_message_mask:
            _save_message(msg, outstring, save_headers=True, save_body=True)

    for content_type in masks:
        if content_type in g.error_mask:
            raise ValueError("content type %s prohibited" % ctype)

    output_headers(msg)

    # Preserve the first part, it is probably not a RFC822-message.
    if msg.preamble:
        # Usually it is just a few lines of text (MIME warning).
        output(msg.preamble)
    if msg.preamble is not None:
        output(os.linesep)

    first_subpart = True
    for subpart in msg.get_payload():
        if boundary:
            if first_subpart:
                first_subpart = False
            else:
                output(os.linesep)
            output("--%s%s" % (boundary, os.linesep))

        # Recursively decode all parts of the subpart
        decode_message(subpart)

    if boundary:
        output("%s--%s--%s" % (os.linesep, boundary, os.linesep))

    if msg.epilogue:
        output(msg.epilogue)


def decode_message(msg):
    "Decode message"

    if msg.is_multipart():
        decode_multipart(msg)
    elif len(msg):  # Simple one-part message (there are headers) - decode it
        decode_part(msg)
    else:  # Not a message, just text - copy it literally
        output(msg.as_string())


def open_output_file(filename):
    fullpath = os.path.abspath(os.path.join(g.destination_dir, filename))
    full_dir = os.path.dirname(fullpath)
    create = not os.path.isdir(full_dir)
    if create:
        os.makedirs(full_dir)
    try:
        return open(fullpath, 'wb')
    except Exception:
        if create:
            shutil.rmtree(full_dir)
        raise
