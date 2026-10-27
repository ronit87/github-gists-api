"""Small HTTP-level tests; GitHub is mocked so tests are repeatable."""
import http.client
import json
import threading
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message

from app import GistsHandler


@contextmanager
def running_server():
    from http.server import HTTPServer

    server = HTTPServer(("127.0.0.1", 0), GistsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def get_json(port, path):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


class GistsAPITests(unittest.TestCase):
    @patch("app.urlopen")
    def test_returns_gists_from_github(self, mock_urlopen):
        expected = [{"id": "123", "public": True}]
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(expected).encode()

        with running_server() as port:
            status, body = get_json(port, "/octocat")

        self.assertEqual(status, 200)
        self.assertEqual(body, expected)
        self.assertIn("/users/octocat/gists", mock_urlopen.call_args.args[0].full_url)

    @patch("app.urlopen")
    def test_unknown_github_user_returns_404(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://api.github.com/users/missing/gists", 404, "Not Found", Message(), None
        )
        with running_server() as port:
            status, body = get_json(port, "/missing")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"error": "GitHub user not found"})

    @patch("app.urlopen")
    def test_github_failure_returns_502(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("network unavailable")
        with running_server() as port:
            status, body = get_json(port, "/octocat")
        self.assertEqual(status, 502)
        self.assertIn("error", body)

    @patch("app.urlopen")
    def test_invalid_username_does_not_call_github(self, mock_urlopen):
        with running_server() as port:
            status, body = get_json(port, "/bad_name")
        self.assertEqual(status, 400)
        mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
