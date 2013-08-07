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
import mimetypes

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

class PHPApp(object):
    def __init__(self, doc_root=None):
        self.doc_root = doc_root

        if doc_root:
            self.cwd = os.path.join(HERE, doc_root)
        else:
            self.cwd = HERE

    def _abs_file_path(self, path):
        return os.path.join(self.cwd, path)

    def __call__(self, environ, start_response):
        php_env = {}
        content = None
        file_path, path_info, query_string = parse_url(environ['PATH_INFO'])
        php_env['PHP_SELF'] = file_path + path_info
        php_env['REMOTE_ADDR'] = environ.get('REMOTE_ADDR', '')

        file_path = self._abs_file_path(file_path)
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, 'index.php')

        extension = file_path.split('/')[-1][-3:]
        if extension != 'php':
            return self.serve_static(environ, start_response, file_path)

        php_args = ['php5-cgi', file_path]
        # REDIRECT_STATUS must be set. See:
        # http://php.net/manual/en/security.cgi-bin.force-redirect.php
        php_env['REDIRECT_STATUS'] = '1'
        php_env['REQUEST_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
        php_env['PATH_INFO'] = path_info
        php_env['QUERY_STRING'] = environ['QUERY_STRING']
        php_env['SCRIPT_FILENAME'] = os.path.join(HERE, file_path)
        php_env['SCRIPT_NAME'] = ''
        php_env['HTTP_HOST'] = environ['HTTP_HOST']
        php_env['SERVER_SOFTWARE'] = 'phpdev.py'
        php_env['HTTP_COOKIE'] = environ.get('HTTP_COOKIE', '')

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
                                 stderr=subprocess.PIPE, env=php_env, cwd=self.cwd)
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

    def serve_static(self, environ, start_response, file_path):
        if not os.path.exists(file_path):
            start_response("404 Not Found", [('Content-type', 'text/plain')])
            return ['Not Found',]

        mimetype, encoding = mimetypes.guess_type(file_path)
        size = os.path.getsize(file_path)
        headers = [
            ("Content-type", mimetype if mimetype else 'text/plain'),
            ("Content-length", str(size)),
        ]

        start_response("200 OK", headers)
        return self.send_file(file_path, size)

    def send_file(self, file_path, size):
        BLOCK_SIZE = 4096
        fh = open(file_path, 'r')
        while True:
            block = fh.read(BLOCK_SIZE)
            if not block:
                fh.close()
                break
            yield block

if __name__ == '__main__':
    application = PHPApp()
    server = make_server('0.0.0.0', 8080, application)
    print "Running at http://127.0.0.1:8080 ..."
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
