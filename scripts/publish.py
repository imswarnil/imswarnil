#!/usr/bin/env python3
"""Commit the regenerated assets through the GitHub Git Data API.

`git push` from Actions is rejected by this repo with an opaque server-side
`fatal error in commit_refs`, so the refresh job builds the commit over the API
instead — same token, one atomic commit, no working tree involved.
"""
import base64, json, os, ssl, sys, urllib.error, urllib.request
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
REPO   = os.environ.get("GITHUB_REPOSITORY", "imswarnil/imswarnil")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
TOKEN  = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
API    = "https://api.github.com"


def ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def call(method, path, body=None):
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "imswarnil-profile"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def main():
    if not TOKEN:
        sys.exit("set GH_TOKEN (or GITHUB_TOKEN)")

    paths = sorted(p for p in (ROOT / "assets").glob("*.svg"))
    if not paths:
        sys.exit("no assets to publish")

    ref  = call("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    head = ref["object"]["sha"]
    base_tree = call("GET", f"/repos/{REPO}/git/commits/{head}")["tree"]["sha"]

    tree = []
    for p in paths:
        blob = call("POST", f"/repos/{REPO}/git/blobs", {
            "content": base64.b64encode(p.read_bytes()).decode(), "encoding": "base64"})
        tree.append({"path": str(p.relative_to(ROOT)), "mode": "100644",
                     "type": "blob", "sha": blob["sha"]})

    new_tree = call("POST", f"/repos/{REPO}/git/trees",
                    {"base_tree": base_tree, "tree": tree})
    if new_tree["sha"] == base_tree:
        print("assets unchanged — nothing to commit")
        return

    commit = call("POST", f"/repos/{REPO}/git/commits", {
        "message": "Refresh cards", "tree": new_tree["sha"], "parents": [head]})
    call("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"]})
    print("committed", commit["sha"][:7])


if __name__ == "__main__":
    main()
