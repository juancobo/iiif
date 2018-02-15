"""Test code for iiif.flask_utils.py."""
import unittest
import argparse
import flask
import os.path
import re  # needed because no assertRegexpMatches in 2.6
import json
from iiif.flask_utils import (Config, html_page, top_level_index_page, identifiers,
    prefix_index_page, host_port_prefix,
    osd_page_handler, IIIFHandler,
    parse_authorization_header, parse_accept_header, make_prefix,
    split_comma_argument, add_shared_configs, add_handler)
from iiif.auth_basic import IIIFAuthBasic
from iiif.manipulator import IIIFManipulator


class TestAll(unittest.TestCase):
    """Tests."""

    def setUp(self):
        """Create a test Flask app which we can use for context."""
        self.test_app = flask.Flask('TestApp')

    def test01_Config(self):
        """Test Config class."""
        c1 = Config()
        c1.a = 'a'
        c1.b = 'b'
        c2 = Config(c1)
        self.assertEqual(c2.a, 'a')
        self.assertEqual(c2.b, 'b')

    def test11_html_page(self):
        """Test HTML page wrapper."""
        html = html_page('TITLE', 'BODY')
        self.assertTrue('<h1>TITLE</h1>' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('BODY</body>' in html)  # FIXME - use assertIn when 2.6 dropped

    def test12_top_level_index_page(self):
        """Test top_level_index_page()."""
        c = Config()
        c.host = 'ex.org'
        c.prefixes = {'pa1a': 'pa1b', 'pa2a': 'pa2b'}
        html = top_level_index_page(c)
        self.assertTrue('ex.org' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('pa1a'in html)  # FIXME - use assertIn when 2.6 dropped

    def test13_identifiers(self):
        """Test identifiers()."""
        c = Config()
        # Generator case
        c.klass_name = 'gen'
        c.generator_dir = os.path.join(os.path.dirname(__file__), '../iiif/generators')
        ids = identifiers(c)
        self.assertTrue('sierpinski_carpet' in ids)  # FIXME - use assertIn when 2.6 dropped
        self.assertFalse('red-19000x19000' in ids)  # FIXME - use assertIn when 2.6 dropped
        # Non-gerenator case
        c = Config()
        c.klass_name = 'anything-not-gen'
        c.image_dir = os.path.join(os.path.dirname(__file__), '../testimages')
        ids = identifiers(c)
        self.assertFalse('sierpinski_carpet' in ids)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('red-19000x19000' in ids)  # FIXME - use assertIn when 2.6 dropped

    def test14_prefix_index_page(self):
        """Test prefix_index_page()."""
        c = Config()
        c.client_prefix = 'pfx'
        c.host = 'ex.org'
        c.api_version = '2.1'
        c.manipulator = 'pil'
        c.auth_type = 'none'
        c.include_osd = True
        c.klass_name = 'pil'
        c.image_dir = os.path.join(os.path.dirname(__file__), '../testimages')
        html = prefix_index_page(c)
        self.assertTrue('/pfx/' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('osd.html' in html)  # FIXME - use assertIn when 2.6 dropped
        # No OSD
        c.include_osd = False
        html = prefix_index_page(c)
        self.assertTrue('/pfx/' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertFalse('osd.html' in html)  # FIXME - use assertIn when 2.6 dropped

    def test15_host_port_prefix(self):
        """Test host_port_prefix()."""
        self.assertEqual(host_port_prefix('ex.org', 80, 'a'), 'http://ex.org/a')
        self.assertEqual(host_port_prefix('ex.org', 8888, 'a'), 'http://ex.org:8888/a')
        self.assertEqual(host_port_prefix('ex.org', 80, None), 'http://ex.org')

# Test Flask handlers

    def test20_osd_page_handler(self):
        """Test osd_page_handler() -- rather trivial check it runs with expected params."""
        c = Config()
        c.api_version = '2.1'
        with self.test_app.app_context():
            resp = osd_page_handler(c, 'an-unusual-id', 'a-prefix')
            html = resp.response[0]
            # Trivial tests on content...
            self.assertTrue(b'openseadragon.min.js' in html)
            self.assertTrue(b'an-unusual-id' in html)

    def test21_IIIFHandler_init(self):
        """Test IIIFHandler class init."""
        # No auth
        c = Config()
        c.api_version = '2.1'
        i = IIIFHandler(prefix='/p', identifier='i', config=c,
                        klass=IIIFManipulator, auth=None)
        self.assertTrue(i.manipulator.api_version, '2.1')
        # Basic auth
        a = IIIFAuthBasic()
        c.host = 'example.org'
        c.port = 80
        c.prefix = '/p'
        i = IIIFHandler(prefix='/p', identifier='i', config=c,
                        klass=IIIFManipulator, auth=a)
        self.assertTrue(i.manipulator.api_version, '2.1')
    
    def test22_IIIFHandler_json_mime_type(self):
        """Test IIIFHandler.json_mime_type()."""
        # No auth, no test for API 1.0
        c = Config()
        c.api_version = '1.0'
        i = IIIFHandler(prefix='/p', identifier='i', config=c,
                        klass=IIIFManipulator, auth=None)
        self.assertEqual(i.json_mime_type, "application/json")
        # No auth, connecg for API 1.1       
        c = Config()
        c.api_version = '1.1'
        i = IIIFHandler(prefix='/p', identifier='i', config=c,
                        klass=IIIFManipulator, auth=None)
        # https://www.python.org/dev/peps/pep-0333/#environ-variables
        environ = dict()
        environ['REQUEST_METHOD'] = 'GET'
        environ['SCRIPT_NAME'] = ''
        environ['PATH_INFO'] = '/'
        environ['SERVER_NAME'] = 'ex.org'
        environ['SERVER_PORT'] = '80'
        environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
        environ['wsgi.url_scheme'] = 'http'
        with self.test_app.request_context(environ):
            self.assertEqual(i.json_mime_type, "application/json")
        environ['HTTP_ACCEPT'] = 'application/ld+json'
        with self.test_app.request_context(environ):
            self.assertEqual(i.json_mime_type, "application/ld+json")        
        environ['HTTP_ACCEPT'] = 'text/plain'
        with self.test_app.request_context(environ):
            self.assertEqual(i.json_mime_type, "application/json")        

    def test51_parse_authorization_header(self):
        """Test parse_authorization_header."""
        # Garbage
        self.assertEqual(parse_authorization_header(''), None)
        self.assertEqual(parse_authorization_header('junk'), None)
        self.assertEqual(parse_authorization_header(
            'junk and more junk'), None)
        # Valid Basic auth, from <https://www.ietf.org/rfc/rfc2617.txt>
        self.assertEqual(parse_authorization_header('Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='),
                         {'type': 'basic', 'username': 'Aladdin', 'password': 'open sesame'})
        self.assertEqual(parse_authorization_header('bASiC QWxhZGRpbjpvcGVuIHNlc2FtZQ=='),
                         {'type': 'basic', 'username': 'Aladdin', 'password': 'open sesame'})
        # Valid Digest auth, from <https://www.ietf.org/rfc/rfc2617.txt>
        self.assertEqual(parse_authorization_header(
            'Digest username="Mufasa", '
            'realm="testrealm@host.com", '
            'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
            'uri="/dir/index.html", '
            'qop=auth, nc=00000001, cnonce="0a4f113b", '
            'response="6629fae49393a05397450978507c4ef1", '
            'opaque="5ccc069c403ebaf9f0171e9517f40e41"'),
            {'type': 'digest', 'username': 'Mufasa',
             'nonce': 'dcd98b7102dd2f0e8b11d0f600bfb0c093',
             'realm': 'testrealm@host.com', 'qop': 'auth',
             'cnonce': '0a4f113b', 'nc': '00000001',
             'opaque': '5ccc069c403ebaf9f0171e9517f40e41',
             'uri': '/dir/index.html',
             'response': '6629fae49393a05397450978507c4ef1'})
        # Error cases
        self.assertEqual(parse_authorization_header('basic ZZZ'), None)
        self.assertEqual(parse_authorization_header('Digest badpair'), None)
        self.assertEqual(parse_authorization_header('Digest badkey="a"'), None)
        self.assertEqual(parse_authorization_header('Digest username="a", '
            'realm="r", nonce="n", uri="u", response="rr", qop="no_nc"'), None)

    def test52_parse_accept_header(self):
        """Test parse_accept_header."""
        accepts = parse_accept_header("text/xml")
        self.assertEqual(len(accepts), 1)
        self.assertEqual(accepts[0], ('text/xml', (), 1.0))
        accepts = parse_accept_header("text/xml;q=0.5")
        self.assertEqual(len(accepts), 1)
        self.assertEqual(accepts[0], ('text/xml', (), 0.5))
        accepts = parse_accept_header("text/xml;q=0.5, text/html;q=0.6")
        self.assertEqual(len(accepts), 2)
        self.assertEqual(accepts[0], ('text/html', (), 0.6))
        self.assertEqual(accepts[1], ('text/xml', (), 0.5))

    def test58_make_prefix(self):
        """Test make_prefix."""
        self.assertEqual(make_prefix('vv', 'mm', None), 'vv_mm')
        self.assertEqual(make_prefix('v2', 'm2', 'none'), 'v2_m2')
        self.assertEqual(make_prefix('v3', 'm3', 'a'), 'v3_m3_a')

    def test59_split_comma_argument(self):
        """Test split_comma_argument()."""
        self.assertEqual(split_comma_argument(''), [])
        self.assertEqual(split_comma_argument('a,b'), ['a','b'])
        self.assertEqual(split_comma_argument('a,b,cccccccccc,,,'), ['a','b','cccccccccc'])

    def test60_add_shared_configs(self):
        """Test add_shared_configs() - just check it runs."""
        p = argparse.ArgumentParser()
        add_shared_configs(p)
        self.assertTrue('--include-osd' in p.format_help())

    def test61_add_handler(self):
        """Test add_handler."""
        c = Config()
        c.klass_name = 'pil'
        c.api_version = '2.1'
        c.include_osd = False
        c.gauth_client_secret_file = 'file'
        c.access_cookie_lifetime = 10
        c.access_token_lifetime = 10
        # Auth types
        for auth in ('none', 'gauth', 'basic', 'clickthrough', 'kiosk', 'external'):
            c.auth_type = auth
            c.prefix = 'pfx1_' + auth
            c.client_prefix = c.prefix
            self.assertTrue(add_handler(self.test_app, Config(c)))
        # Manipulator types
        c.auth_type = 'none'
        for klass in ('pil', 'netpbm', 'gen', 'dummy'):
            c.klass_name = klass
            c.prefix = 'pfx2_' + klass
            c.client_prefix = c.prefix
            self.assertTrue(add_handler(self.test_app, Config(c)))
        # Include OSD
        c.include_osd = True
        self.assertTrue(add_handler(self.test_app, Config(c)))
        # Bad cases
        c.auth_type = 'bogus'
        self.assertFalse(add_handler(self.test_app, Config(c)))
        c.auth_type = 'none'
        c.klass_name = 'no-klass'
        self.assertFalse(add_handler(self.test_app, Config(c)))

