#!/usr/bin/env python3
"""
Server guard tests for MarkVue (stdlib only).

    python -m unittest tests/test_server.py -v

Starts the embedded HTTP server from markvue_app.py on a free loopback port
and checks that every endpoint behaves and that the guards hold:
only MarkVue.html is served, loopback Host header required, /api/save only
writes files MarkVue opened and only from same-origin JSON, /asset/ never
leaves the document folder.
"""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.client import HTTPConnection

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import markvue_app as app  # noqa: E402


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.docdir = os.path.join(cls.tmp.name, 'doc')
        os.makedirs(cls.docdir)
        cls.doc = os.path.join(cls.docdir, 'note.md')
        with open(cls.doc, 'w', encoding='utf-8') as f:
            f.write('# Note\n\n![i](img.png)\n')
        with open(os.path.join(cls.docdir, 'img.png'), 'wb') as f:
            f.write(b'PNG')
        cls.secret = os.path.join(cls.tmp.name, 'secret.txt')
        with open(cls.secret, 'w') as f:
            f.write('SECRET')

        app.DOC = app.DocState()
        app.load_initial_file(cls.doc)
        cls.port = app.find_free_port(28737)
        resource_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        threading.Thread(target=app.start_server, args=(cls.port, resource_dir), daemon=True).start()
        assert app.wait_for_server(cls.port), 'server did not start'
        cls.base = f'http://127.0.0.1:{cls.port}'

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # --- helpers ---

    def get(self, path, headers=None, raw_path=False):
        """Return (status, body, content_type). raw_path sends the path verbatim (no normalisation)."""
        if raw_path:
            c = HTTPConnection('127.0.0.1', self.port, timeout=5)
            c.putrequest('GET', path, skip_host=True)
            c.putheader('Host', (headers or {}).get('Host', f'127.0.0.1:{self.port}'))
            c.endheaders()
            r = c.getresponse()
            body = r.read()
            status, ctype = r.status, r.getheader('Content-Type')
            c.close()
            return status, body, ctype
        req = urllib.request.Request(self.base + path, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read(), r.headers.get('Content-Type')
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get('Content-Type')

    def post(self, path, body, headers):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method='POST')
        def parse(raw):
            try:
                return json.loads(raw or b'{}')
            except ValueError:
                return {'raw': raw.decode('utf-8', 'replace')}
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, parse(r.read())
        except urllib.error.HTTPError as e:
            return e.code, parse(e.read())

    # --- tests ---

    def test_root_serves_html_only(self):
        status, body, ctype = self.get('/')
        self.assertEqual(status, 200)
        self.assertIn('text/html', ctype)
        self.assertIn(b'<title>MarkVue</title>', body)
        for p in ('/markvue_app.py', '/README.md', '/LICENSE', '/.git/config'):
            self.assertEqual(self.get(p)[0], 404, p)
        self.assertEqual(self.get('/../README.md', raw_path=True)[0], 404)

    def test_host_header_guard(self):
        self.assertEqual(self.get('/', headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.get('/', headers={'Host': f'localhost:{self.port}'})[0], 200)

    def test_initial_file(self):
        status, body, _ = self.get('/api/initial-file')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data['filename'], 'note.md')
        self.assertEqual(data['path'], os.path.abspath(self.doc))
        self.assertTrue(data['content'].startswith('# Note'))

    def test_asset_confined_to_document_folder(self):
        status, body, ctype = self.get('/asset/img.png')
        self.assertEqual((status, body), (200, b'PNG'))
        self.assertIn('image/png', ctype)
        self.assertEqual(self.get('/asset/../secret.txt', raw_path=True)[0], 403)
        self.assertEqual(self.get('/asset/..%2Fsecret.txt')[0], 403)
        self.assertEqual(self.get('/asset/missing.png')[0], 404)

    def test_save_rejects_foreign_origin_and_wrong_content_type(self):
        status, data = self.post('/api/save', {'path': self.doc, 'content': 'x'},
                                 {'Content-Type': 'application/json', 'Origin': 'http://evil.example'})
        self.assertEqual(status, 403, data)
        status, data = self.post('/api/save', {'path': self.doc, 'content': 'x'},
                                 {'Content-Type': 'text/plain'})
        self.assertEqual(status, 415, data)
        with open(self.doc, encoding='utf-8') as f:
            self.assertTrue(f.read().startswith('# Note'), 'file must be untouched')

    def test_save_rejects_paths_markvue_did_not_open(self):
        status, data = self.post('/api/save', {'path': self.secret, 'content': 'pwned'},
                                 {'Content-Type': 'application/json'})
        self.assertEqual(status, 403, data)
        with open(self.secret) as f:
            self.assertEqual(f.read(), 'SECRET')

    def test_save_writes_opened_file(self):
        status, data = self.post('/api/save', {'path': self.doc, 'content': '# Saved\n'},
                                 {'Content-Type': 'application/json', 'Origin': self.base})
        self.assertEqual(status, 200, data)
        self.assertTrue(data['ok'])
        with open(self.doc, encoding='utf-8') as f:
            self.assertEqual(f.read(), '# Saved\n')

    def test_unknown_routes_404(self):
        self.assertEqual(self.get('/api/nope')[0], 404)
        self.assertEqual(self.post('/api/other', {}, {'Content-Type': 'application/json'})[0], 404)


if __name__ == '__main__':
    unittest.main()
