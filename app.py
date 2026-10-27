"""Small HTTP API that returns a GitHub user's public Gists."""
import json
import logging
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
GITHUB_URL = "https://api.github.com"
USERNAME = re.compile(r"^[A-Za-z0-9-]{1,39}$")


def get_public_gists(username):
    """Fetch public Gists from GitHub and return the decoded JSON list."""
    request = Request(
        f"{GITHUB_URL}/users/{username}/gists",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-gists-takehome",
        },
    )
    try:
        with urlopen(request, timeout=5) as response:
            gists = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            raise ValueError("GitHub user not found") from error
        raise RuntimeError("GitHub API request failed") from error
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError("Could not connect to GitHub API") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("GitHub returned invalid JSON") from error

    if not isinstance(gists, list):
        raise RuntimeError("GitHub returned an unexpected response")
    return gists


class GistsHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # The only supported route is /<username>.
        username = self.path.strip("/")
        if not username or "/" in username:
            self.send_json(404, {"error": "Use GET /<username>"})
            return
        if not USERNAME.fullmatch(username):
            self.send_json(400, {"error": "Invalid GitHub username"})
            return

        logging.info("Fetching public Gists for %s", username)
        try:
            self.send_json(200, get_public_gists(username))
        except ValueError as error:
            self.send_json(404, {"error": str(error)})
        except RuntimeError as error:
            logging.warning("%s", error)
            self.send_json(502, {"error": str(error)})

    def log_message(self, format, *args):
        logging.info("%s - %s", self.address_string(), format % args)


if __name__ == "__main__":
    logging.info("Starting server on port 8080")
    HTTPServer(("0.0.0.0", 8080), GistsHandler).serve_forever()
