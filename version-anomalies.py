#!/usr/bin/env python3

import argparse
import os
import re
import sys
import urllib.request

import calm.version


def parse_setup_ini(contents):
    s = {}

    for l in contents.splitlines():
        if l.startswith('@'):
            p = l[2:]
        elif l.startswith('version:'):
            v = l[9:]
            # only note the first version: line (the 'current' version)
            if p not in s:
                s[p] = calm.version.SetupVersion(v)

    return s


parser = argparse.ArgumentParser(description='Make setup.ini')
parser.add_argument('--arch', action='store', required=True, choices=['x86', 'x86_64'])
(args) = parser.parse_args()

if args.arch == 'x86':
    index_url = "http://ctm.crouchingtigerhiddenfruitbat.org/pub/cygwin/circa/index.html"
else:
    index_url = "http://ctm.crouchingtigerhiddenfruitbat.org/pub/cygwin/circa/64bit/index.html"

# read index, build list of setup.uni URLs
urls = []
html = urllib.request.urlopen(index_url).read().decode()
for l in html.splitlines():
    m = re.search('<td>(http.*)</td>', l)
    if m:
        urls.append(m.group(1) + '/setup.ini')

print("%-23s %-17s %-17s %s" % ('package','version','version','after circa'))

# for each setup.ini URL, fetch, parse and compare with previous
prev = None
for u in urls:
    circa = re.search('(circa/.*)/setup.ini', u).group(1)
    cache_fn = os.path.join('cache', u.replace('http://', '').replace(os.path.sep, '_'))

    if not os.path.isfile(cache_fn):
        (filename, headers) = urllib.request.urlretrieve(u, cache_fn)
        print('fetching %s' % u, file=sys.stderr)
    else:
        filename = cache_fn
        # print('%s from cache' % filename, file=sys.stderr)

    # parse it
    with open(filename, errors='ignore') as f:
        curr = parse_setup_ini(f.read())

    # look for versions which went backwards and packages which disappeared
    if prev:
        for k in curr:
            if k not in prev:
                # print("'%s' disappeared in %s" % (k, filename))
                continue

            vc = curr[k]
            vp = prev[k]

            if vc > vp:
                print("%-23s %-17s %-17s %s" % (k, vc._version_string, vp._version_string, circa))
                # don't report this again
                prev[k] = curr[k]
    else:
        # first becomes previous
        prev = curr
