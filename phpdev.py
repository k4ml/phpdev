"""
Copyright (c) 2013 Mohd. Kamal Bin Mustafa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import sys
import urllib
import httplib
import subprocess
import cStringIO
import traceback

from wsgiref.simple_server import make_server

HERE = os.path.abspath(os.path.dirname(__file__))

def application(environ, start_response):
    content = None
    php_script = environ['PATH_INFO'].lstrip('/')
    php_args = ['php5-cgi', php_script]
    php_env = {}
    # REDIRECT_STATUS must be set. See:
    # http://php.net/manual/en/security.cgi-bin.force-redirect.php
    php_env['REDIRECT_STATUS'] = '1'
    php_env['REQUEST_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
    php_env['PATH_INFO'] = ''
    php_env['QUERY_STRING'] = environ['QUERY_STRING']
    php_env['SCRIPT_FILENAME'] = os.path.join(HERE, php_script)

    # Construct the partial URL that PHP expects for REQUEST_URI
    # (http://php.net/manual/en/reserved.variables.server.php) using part of
    # the process described in PEP-333
    # (http://www.python.org/dev/peps/pep-0333/#url-reconstruction).
    php_env['REQUEST_URI'] = urllib.quote(environ['PATH_INFO'])
    if php_env['QUERY_STRING']:
        php_env['REQUEST_URI'] += '?' + php_env['QUERY_STRING']

    try:
        p = subprocess.Popen(php_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=php_env, cwd=HERE)
    except Exception as e:
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [traceback.format_exc()]

    stdout, stderr = p.communicate(content)

    message = httplib.HTTPMessage(cStringIO.StringIO(stdout))
    assert 'Content-Type' in message, 'invalid CGI response: %r' % stdout

    if 'Status' in message:
        status = message['Status']
        del message['Status']
    else:
        status = '200 OK'

    # Ensures that we avoid merging repeat headers into a single header,
    # allowing use of multiple Set-Cookie headers.
    headers = []
    for name in message:
        for value in message.getheaders(name):
            headers.append((name, value))

    start_response(status, headers)
    return [message.fp.read()]

if __name__ == '__main__':
    server = make_server('0.0.0.0', 8080, application)
    print "Running at http://127.0.0.1:8080 ..."
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
