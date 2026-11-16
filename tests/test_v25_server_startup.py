#!/usr/bin/env python3
"""Server startup must not depend on reverse DNS for a LAN address."""
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class ServerStartupTests(unittest.TestCase):
    def test_http_server_binds_without_reverse_dns(self):
        with patch.object(socket, "getfqdn", side_effect=AssertionError("reverse DNS must not be called")):
            httpd = server.MaClasseHTTPServer(("127.0.0.1", 0), server.Handler)
        try:
            self.assertEqual(httpd.server_name, "127.0.0.1")
            self.assertGreater(httpd.server_port, 0)
            self.assertEqual(httpd.server_address[0], "127.0.0.1")
        finally:
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
