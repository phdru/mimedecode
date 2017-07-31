#! /usr/bin/env python
from __future__ import print_function

import sys
from m_lib.net.www.html import HTMLFilter

PY2 = sys.version_info[0] < 3
if PY2:
    with open(sys.argv[1], 'r') as f:
        html = f.read()
else:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html = f.read()

filter = HTMLFilter()
filter.feed(html)
filter.close()

if PY2:
    print(filter.accumulator)
else:
    if not isinstance(filter.accumulator, bytes):
        filter.accumulator = filter.accumulator.encode('utf-8')
    sys.stdout.buffer.write(filter.accumulator + b'\n')
