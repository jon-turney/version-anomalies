#!/usr/bin/env python3

import argparse
import os
import re
import urllib.request

import calm.version

def parse_setup_ini(contents):
    s = {}

    for l in contents.splitlines():
        if l.startswith('@'):
            p = l[2:]
            s[p] = []
        elif l.startswith('version:'):
            v = l[9:]
            s[p].append(v)

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

# for each setup.ini URL, fetch, parse and compare with previous
prev = None
for u in urls:
    circa = re.search('(circa/.*)/setup.ini', u).group(1)
    cache_fn = os.path.join('cache', u.replace('http://', '').replace(os.path.sep, '_'))

    if not os.path.isfile(cache_fn):
        (filename, headers) = urllib.request.urlretrieve(u, cache_fn)
        print('fetching %s' % filename)
    else:
        filename = cache_fn
#        print('%s from cache' % filename)

    # parse it
    with open(filename, errors='ignore') as f:
        curr = parse_setup_ini(f.read())

    # look for versions which went backwards and packages which disappeared
    if prev:
        for k in curr:
            if k not in prev:
#                print("'%s' disappeared in %s" % (k, filename))
                continue

            if len(curr[k]) < 1:
#                print("'%s' doesn't have any versions in %s" % (k, circa))
                continue

            vc = calm.version.SetupVersion(curr[k][0])
            vp = calm.version.SetupVersion(prev[k][0])

            if vc > vp:
                print("'%s' version went backwards from '%s' to '%s' after %s" % (k, curr[k][0], prev[k][0], circa))
                # don't report this again
                prev[k] = curr[k]
    else:
    # first becomes previous
        prev = curr
