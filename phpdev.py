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
import posixpath

from urlparse import urlparse
from wsgiref.simple_server import make_server
from SimpleHTTPServer import SimpleHTTPRequestHandler

HERE = os.path.abspath(os.path.dirname(__file__))

def parse_url(url):
    po = urlparse(url) 
    file_path = po.path.lstrip('/')
    file_path_part = []
    path_info_part = []
    php_part_done = False
    for segment in file_path.split('/'):
        if '.php' in segment:
            php_part_done = True
            file_path_part.append(segment)
            continue
        if not php_part_done:
            file_path_part.append(segment)
        else:
            path_info_part.append(segment)

    path_info = '/'.join(path_info_part)
    file_path = '/'.join(file_path_part)
    query_string = po.query

    return file_path, path_info, query_string

def application(environ, start_response):
    content = None
    file_path, path_info, query_string = parse_url(environ['PATH_INFO'])
    php_args = ['php5-cgi', file_path]
    php_env = {}
    # REDIRECT_STATUS must be set. See:
    # http://php.net/manual/en/security.cgi-bin.force-redirect.php
    php_env['REDIRECT_STATUS'] = '1'
    php_env['REQUEST_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
    php_env['PATH_INFO'] = path_info
    php_env['QUERY_STRING'] = environ['QUERY_STRING']
    php_env['SCRIPT_FILENAME'] = os.path.join(HERE, file_path)

    # Construct the partial URL that PHP expects for REQUEST_URI
    # (http://php.net/manual/en/reserved.variables.server.php) using part of
    # the process described in PEP-333
    # (http://www.python.org/dev/peps/pep-0333/#url-reconstruction).
    php_env['REQUEST_URI'] = urllib.quote(environ['PATH_INFO'])
    if php_env['QUERY_STRING']:
        php_env['REQUEST_URI'] += '?' + php_env['QUERY_STRING']

    if 'CONTENT_TYPE' in environ:
        php_env['CONTENT_TYPE'] = environ['CONTENT_TYPE']
        php_env['HTTP_CONTENT_TYPE'] = environ['CONTENT_TYPE']

    # POST data
    if 'CONTENT_LENGTH' in environ:
        if environ['CONTENT_LENGTH'].strip():
            php_env['CONTENT_LENGTH'] = environ['CONTENT_LENGTH']
            php_env['HTTP_CONTENT_LENGTH'] = environ['CONTENT_LENGTH']
            content = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))

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

class StaticApp(SimpleHTTPRequestHandler):
    """WSGI application for serving static files.

    Original code - https://raw.github.com/webpy/webpy/master/web/httpserver.py
    """
    def __init__(self, environ, start_response):
        self.headers = []
        self.environ = environ
        self.start_response = start_response

    def send_response(self, status, msg=""):
        self.status = str(status) + " " + msg

    def send_header(self, name, value):
        self.headers.append((name, value))

    def end_headers(self):
        pass

    def log_message(*a): pass

    def __iter__(self):
        environ = self.environ

        self.path = environ.get('PATH_INFO', '')
        self.client_address = environ.get('REMOTE_ADDR','-'), \
                              environ.get('REMOTE_PORT','-')
        self.command = environ.get('REQUEST_METHOD', '-')

        from cStringIO import StringIO
        self.wfile = StringIO() # for capturing error

        try:
            path = self.translate_path(self.path)
            etag = '"%s"' % os.path.getmtime(path)
            client_etag = environ.get('HTTP_IF_NONE_MATCH')
            self.send_header('ETag', etag)
            if etag == client_etag:
                self.send_response(304, "Not Modified")
                self.start_response(self.status, self.headers)
                raise StopIteration
        except OSError:
            pass # Probably a 404

        f = self.send_head()
        self.start_response(self.status, self.headers)

        if f:
            block_size = 16 * 1024
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                yield buf
            f.close()
        else:
            value = self.wfile.getvalue()
            yield value

class StaticMiddleware:
    """WSGI middleware for serving static files."""
    def __init__(self, app, prefix='/static/'):
        self.app = app
        self.prefix = prefix
        
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)
        file_path, path_info, query_string = parse_url(path)
        extension = file_path.split('/')[-1][-3:]

        if extension != 'php':
            return StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2

if __name__ == '__main__':
    server = make_server('0.0.0.0', 8080, StaticMiddleware(application))
    print "Running at http://127.0.0.1:8080 ..."
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
