#! /usr/bin/env python

import sys
from m_lib.net.www.html import HTMLFilter

with open(sys.argv[1], 'r') as f:
    html = f.read()

filter = HTMLFilter()
filter.feed(html)
filter.close()

print filter.accumulator
