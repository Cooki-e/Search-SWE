import json
import shutil
import unittest

from scripts.docker_dns import create_overlay, parse_servers


class DockerDNSTests(unittest.TestCase):
    def test_servers(self):
        self.assertEqual(parse_servers('198.18.254.30, 198.18.254.31,198.18.254.30'),
                         ['198.18.254.30', '198.18.254.31'])

    def test_reject_invalid_servers(self):
        for value in ('', '127.0.0.53', '::1', '1.1.1.1;echo bad', 'example.org', '0.0.0.0', '224.0.0.1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_servers(value)

    def test_overlay_only_changes_sidecar(self):
        path = create_overlay(['198.18.254.30'])
        try:
            obj = json.loads(path.read_text())
            self.assertEqual(list(obj['services']), ['harbor-docker-egress-control-sidecar'])
            sidecar = obj['services']['harbor-docker-egress-control-sidecar']
            self.assertEqual(sidecar['dns'], ['198.18.254.30'])
            self.assertTrue(all(v['read_only'] for v in sidecar['volumes']))
            self.assertTrue((path.parent/'network-policy-original').is_file())
        finally:
            shutil.rmtree(path.parent)
