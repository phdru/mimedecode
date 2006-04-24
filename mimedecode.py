#! /usr/local/bin/python -O
"""Decode MIME message.

Author: Oleg Broytmann <phd@phd.pp.ru>
Copyright: (C) 2001-2002 PhiloSoft Design
License: GPL
"""

__version__ = "1.1.7"


import sys, os
import mimetools

try:
   from cStringIO import StringIO
except ImportError:
   from StringIO import StringIO


import socket
host_name = socket.gethostname()

me = os.path.basename(sys.argv[0])


def usage(code=0):
   sys.stdout.write("""\
Usage: %s [-h|--help] [-V|--version] [-cCDP] [-f charset] [-d header] [-p header:param] [-beit mask] [filename]
""" % me)
   sys.exit(code)


def version():
   sys.stdout.write("""\
BroytMann mimedecode.py version %s
""" % __version__)
   sys.exit(0)


def output(s):
   sys.stdout.write(s)

def output_headers(msg):
   if msg.unixfrom:
      output(msg.unixfrom)
   output("%s\n" % msg)


def recode(s, charset):
   return unicode(s, charset, "replace").encode(GlobalOptions.default_charset, "replace")


def recode2(s, charset):
   if charset and charset <> GlobalOptions.default_charset:
      charset = charset.lower()
      s = recode(s, charset)
   return s


def getparam(msg, header, param):
   "Get parameter from the header; return the header without the parameter, parameter itself and rfc2231 flag"

   if not msg.has_key(header):
      return None, None, 0

   header = msg[header]
   parts = [part.strip() for part in header.split(';')]

   new_parts = [parts[0]] # The header itself
   del parts[0]

   new_value = None
   rfc2231_encoded = 0

   import re, rfc822
   rfc2231_continuation = re.compile("^%s\\*[0-9]+\\*?$" % param)
   rfc2231_header = []

   for part in parts:
      name, value = part.split('=', 1)
      # The code is incomplete. Continuations in rfc2231-encoded paramters
      # (header*1, header*2, etc) are not yet supported
      if (name == param) or (name == param + '*'):
         new_value = rfc822.unquote(value)
         rfc2231_encoded += (name <> param)
      elif rfc2231_continuation.match(name):
         rfc2231_header.append(rfc822.unquote(value))
         rfc2231_encoded = 1
      else:
         new_parts.append(part)

   if rfc2231_header:
      new_value = ''.join(rfc2231_header)

   if new_value is not None:
      return "; ".join(new_parts), new_value, rfc2231_encoded

   return None, None, 0


def decode_header(msg, header):
   "Decode mail header (if exists) and put it back, if it was encoded"

   if msg.has_key(header):
      value = msg[header]
      new_value = decode_rfc2047(value)
      if value <> new_value: # do not bother to touch msg if not changed
         msg[header] = new_value


def decode_header_param(msg, header, param):
   "Decode mail header's parameter (if exists) and put it back, if it was encoded"

   if msg.has_key(header):
      new_value, pstr, rfc2231_encoded = getparam(msg, header, param)
      if pstr is not None:
         if rfc2231_encoded:
            new_str = decode_rfc2231(pstr)
         else:
            new_str = decode_rfc2047(pstr)
         if pstr <> new_str: # do not bother to touch msg if not changed
            msg[header] = "%s; %s=\"%s\"" % (new_value, param, new_str)


def decode_rfc2047(s):
   "Decode string according to rfc2047"

   parts = s.split() # by whitespaces
   new_parts = []
   got_encoded = 0

   for s in parts:
      l = s.split('?')

      if l[0] <> '=' or l[4] <> '=': # assert correct format
         new_parts.append(' ')
         new_parts.append(s) # if not encoded - just put it into output
         got_encoded = 0
         continue

      if not got_encoded:
         new_parts.append(' ') # no space between encoded parts, one space otherwise
         got_encoded = 1

      charset = l[1].lower()
      encoding = l[2].lower()
      s = l[3]

      if '*' in charset:
         charset, language = charset.split('*', 1) # language ignored

      infile = StringIO(s)
      outfile = StringIO()

      if encoding == "b":
         from base64 import decode
      elif encoding == "q":
         from quopri import decode
      else:
         raise ValueError, "wrong encoding `%s' (expected 'b' or 'q')" % encoding

      decode(infile, outfile)
      s = outfile.getvalue()

      if charset == GlobalOptions.default_charset:
         new_parts.append(s) # do not recode
         continue

      s = recode(s, charset)
      new_parts.append(s)

   if new_parts and new_parts[0] == ' ':
      del new_parts[0]
   return ''.join(new_parts)


def decode_rfc2231(s):
   "Decode string according to rfc2231"

   charset, language, s = s.split("'", 2) # language ignored

   i = 0
   result = []

   while i < len(s):
      c = s[i]
      if c == '%': # hex
         i += 1
         c = chr(int(s[i:i+2], 16))
         i += 1
      result.append(c)
      i += 1

   s = ''.join(result)
   s = recode2(s, charset)
   return s


def decode_headers(msg):
   "Decode message headers according to global options"

   for header in GlobalOptions.decode_headers:
      decode_header(msg, header)

   for header, param in GlobalOptions.decode_header_params:
      decode_header_param(msg, header, param)
      if header.lower() == "content-type" and msg.has_key(header):
         # reparse type
         msg.typeheader = msg[header]
         msg.parsetype() # required for plist...
         msg.parseplist() #... and reparse decoded plist


def set_content_type(msg, newtype, charset=None):
   plist = msg.getplist()
   if plist:
      if charset:
         newplist = []
         for p in plist:
            if p.split('=')[0] == "charset":
               p = "charset=%s" % charset
            newplist.append(p)
         plist = newplist

   elif charset:
      plist = ["charset=%s" % charset]

   else:
      plist = []

   if plist and plist[0]: plist.insert(0, '')
   msg["Content-Type"] = "%s%s" % (newtype, ";\n ".join(plist))


caps = None # Globally stored mailcap database; initialized only if needed

def decode_body(msg, s):
   "Decode body to plain text using first copiousoutput filter from mailcap"

   import mailcap, tempfile

   global caps
   if caps is None:
      caps = mailcap.getcaps()

   content_type = msg.gettype()
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
   msg["X-MIME-Body-Autoconverted"] = "from %s to text/plain by %s id %s" % (content_type, host_name, command.split()[0])

   msg.maintype = "text"
   msg.subtype = "plain"
   msg.type = "text/plain"

   return s


def recode_charset(msg, s):
   "Recode charset of the message to the default charset"

   save_charset = charset = msg.getparam("charset")
   if charset and charset <> GlobalOptions.default_charset:
      s = recode2(s, charset)
      content_type = msg.gettype()
      set_content_type(msg, content_type, GlobalOptions.default_charset)
      msg["X-MIME-Charset-Autoconverted"] = "from %s to %s by %s id %s" % (save_charset, GlobalOptions.default_charset, host_name, me)
   return s


def totext(msg, infile):
   "Convert infile (StringIO) content to text"

   if msg.getmaintype() == "multipart": # Recursively decode all parts of the multipart message
      newfile = StringIO("%s\n%s" % (msg, infile.getvalue()))
      decode_file(newfile)
      return

   # Decode body and recode charset
   s = decode_body(msg, infile.getvalue())
   if GlobalOptions.recode_charset:
      s = recode_charset(msg, s)

   output_headers(msg)
   output(s)


def decode_part(msg, infile):
   "Decode one part of the message"

   encoding = msg.getencoding()
   outfile = StringIO()

   if encoding in ('', '7bit', '8bit', 'binary'):
      mimetools.copyliteral(infile, outfile)
   else: # Decode from transfer ecoding to text or binary form
      mimetools.decode(infile, outfile, encoding)
      msg["Content-Transfer-Encoding"] = "8bit"
      msg["X-MIME-Autoconverted"] = "from %s to 8bit by %s id %s" % (encoding, host_name, me)

   decode_headers(msg)

   # Test all mask lists and find what to do with this content type

   for content_type in msg.gettype(), msg.getmaintype()+"/*", "*/*":
      if content_type in GlobalOptions.totext_mask:
         totext(msg, outfile)
         return
      elif content_type in GlobalOptions.binary_mask:
         output_headers(msg)
         output(outfile.getvalue())
         return
      elif content_type in GlobalOptions.ignore_mask:
         output_headers(msg)
         output("\nMessage body of type `%s' skipped.\n" % content_type)
         return
      elif content_type in GlobalOptions.error_mask:
         raise ValueError, "content type `%s' prohibited" % content_type

   # Neither content type nor masks were listed - decode by default
   totext(msg, outfile)


def decode_file(infile, seekable=1):
   "Decode the entire message"

   m = mimetools.Message(infile)
   boundary = m.getparam("boundary")

   if not boundary:
      if not m.getheader("Content-Type"): # Not a message, just text - copy it literally
         output(infile.read())

      else: # Simple one-part message - decode it
         decode_part(m, infile)

   else: # MIME message - decode all parts; may be recursive
      decode_headers(m)
      output_headers(m)

      import multifile
      mf = multifile.MultiFile(infile, seekable)
      mf.push(boundary)

      if not seekable: # Preserve the first part, it is probably not a RFC822-message
         output(mf.read()) # Usually it is just a few lines of text (MIME warning)

      while 1:
         m = mimetools.Message(mf)
         decode_part(m, mf)

         if not mf.next():
            break
         output("\n--%s\n" % boundary)

      mf.pop()
      output("\n--%s--\n" % boundary)


class GlobalOptions:
   default_charset = sys.getdefaultencoding()
   recode_charset = 1 # recode charset of message body

   decode_headers = ["Subject", "From"] # A list of headers to decode
   decode_header_params = [("Content-Type", "name"),
      ("Content-Disposition", "filename")
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
         GlobalOptions.default_charset = value
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

   seekable = 0
   if len(arguments) == 0:
      infile = sys.stdin
   elif len(arguments) <> 1:
      usage(1)
   elif arguments[0] == '-':
      infile = sys.stdin
   else:
      infile = open(arguments[0], 'r')
      seekable = 1

   decode_file(infile, seekable)
