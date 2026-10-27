# GitHub Public Gists API — Take-Home Solution

A small Python HTTP server that fetches a user's **public** Gists from GitHub.
It uses only Python's standard library: no token, database, cache, pagination,
health endpoint, or third-party packages.

## Requirements
- Python 3.12+ to run locally
- Docker to run as a container

## Run locally
```bash
python app.py
```
The service listens on `http://localhost:8080`.

In another terminal:
```bash
curl http://localhost:8080/octocat
```
The response is a JSON list returned by GitHub's public Gists API. The service
does not contain hardcoded Gist data.

## Run automated tests
From the project directory:
```bash
python -m unittest discover -s tests -v
```
Tests mock the GitHub HTTP call, so they run without internet access and do not
depend on GitHub availability or rate limits.

## Build and run with Docker
```bash
docker build -t github-gists-api .
docker run --rm -p 8080:8080 github-gists-api
```
Then call `http://localhost:8080/octocat`.

## Endpoint and errors
- `GET /<username>` — returns the public Gists as a JSON list.
- `400` — invalid username.
- `404` — unsupported route or GitHub user not found.
- `502` — GitHub API/network/response error.

The request to GitHub has a five-second timeout. No authentication is used because
the assignment requires public Gists only.
