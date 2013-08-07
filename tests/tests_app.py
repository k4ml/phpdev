import os

from phpdev import PHPApp
from webtest import TestApp

HERE = os.path.abspath(os.path.dirname(__file__))

class TestPHPApp(object):
    def test_ok(self):
        app = TestApp(PHPApp(doc_root=HERE))
        resp = app.get('/index.php')
        assert resp.status_code == 200, resp.status_code
        assert 'hello world' in resp.body, resp.body

    def test_doc_root_below(self):
        app = TestApp(PHPApp(doc_root=os.path.join(HERE, 'doc_root')))
        resp = app.get('/index.php')
        assert resp.status_code == 200, resp.status_code
        assert 'hello world' in resp.body, resp.body

    def test_static(self):
        app = TestApp(PHPApp(doc_root=os.path.join(HERE, 'doc_root')))
        resp = app.get('/style.css')
        assert resp.status_code == 200, resp.status_code
        assert 'background' in resp.body, resp.body

    def test_static_sub_dir(self):
        app = TestApp(PHPApp(doc_root=os.path.join(HERE, 'doc_root')))
        resp = app.get('/static/style.css')
        assert resp.status_code == 200, resp.status_code
        assert 'background' in resp.body, resp.body
