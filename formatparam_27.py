from email import message
from email import utils


def _formatparam(param, value=None, quote=True):
    """This is _formatparam from Python 2.7"""
    if value is not None and len(value) > 0:
        # A tuple is used for RFC 2231 encoded parameter values where items
        # are (charset, language, value).  charset is a string, not a Charset
        # instance.
        if isinstance(value, tuple):
            # Encode as per RFC 2231
            param += '*'
            value = utils.encode_rfc2231(value[2], value[0], value[1])
        # BAW: Please check this.  I think that if quote is set it should
        # force quoting even if not necessary.
        if quote or message.tspecials.search(value):
            return '%s="%s"' % (param, utils.quote(value))
        else:
            return '%s=%s' % (param, value)
    else:
        return param


# Replace with this _formatparam to avoid re-encoding non-ascii params
message._formatparam = _formatparam
