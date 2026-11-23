#!/usr/bin/env python3
"""PR Review Loopback CLI for New_Veil.

Inspects unresolved GitHub PR review threads, posts replies with commit
references, and resolves threads once addressed.

Examples:
    python scripts/pr_review_loop.py list --pr 5
    python scripts/pr_review_loop.py reply-resolve --thread PRRT_... --message "Fixed in abc1234."
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

OWNER = "kas1987"
REPO = "New_Veil"

LIST_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 10) {
            nodes {
              id
              author { login }
              body
            }
          }
        }
      }
    }
  }
}
"""

REPLY_MUTATION = """
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
    comment { id url }
  }
}
"""

RESOLVE_MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}
"""


def _gh_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, val in variables.items():
        if isinstance(val, int):
            cmd.extend(["-F", f"{key}={val}"])
        else:
            cmd.extend(["-f", f"{key}={val}"])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return json.loads(proc.stdout)


def list_threads(pr_number: int, include_resolved: bool = False) -> list[dict[str, Any]]:
    data = _gh_graphql(LIST_QUERY, {"owner": OWNER, "repo": REPO, "pr": pr_number})
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    out: list[dict[str, Any]] = []
    for node in nodes:
        if not include_resolved and node.get("isResolved"):
            continue
        comments = node.get("comments", {}).get("nodes", [])
        first = comments[0] if comments else {}
        out.append(
            {
                "id": node["id"],
                "isResolved": node["isResolved"],
                "path": node.get("path"),
                "line": node.get("line"),
                "author": (first.get("author") or {}).get("login", "unknown"),
                "body": first.get("body", ""),
                "comment_count": len(comments),
            }
        )
    return out


def reply_and_resolve(thread_id: str, message: str, resolve: bool = True) -> dict[str, Any]:
    reply_res = _gh_graphql(REPLY_MUTATION, {"threadId": thread_id, "body": message})
    resolved = False
    if resolve:
        res_data = _gh_graphql(RESOLVE_MUTATION, {"threadId": thread_id})
        resolved = bool(res_data["data"]["resolveReviewThread"]["thread"]["isResolved"])
    return {
        "thread_id": thread_id,
        "reply_id": reply_res["data"]["addPullRequestReviewThreadReply"]["comment"]["id"],
        "resolved": resolved,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PR review loopback helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List unresolved review threads")
    p_list.add_argument("--pr", type=int, required=True)
    p_list.add_argument("--all", action="store_true", help="Include resolved threads")
    p_list.add_argument("--json", action="store_true", dest="as_json")

    p_rr = sub.add_parser("reply-resolve", help="Reply to a thread and mark it resolved")
    p_rr.add_argument("--thread", required=True)
    p_rr.add_argument("--message", required=True)
    p_rr.add_argument("--no-resolve", action="store_true")

    args = parser.parse_args()
    if args.cmd == "list":
        threads = list_threads(args.pr, include_resolved=args.all)
        if args.as_json:
            print(json.dumps(threads, indent=2))
        else:
            print(f"PR #{args.pr}: {len(threads)} thread(s)")
            for t in threads:
                print(f"- [{t['id']}] {t['path']}:{t['line']} ({t['author']})")
                print(f"  {t['body'][:160].replace(chr(10), ' ')}")
        return 0

    if args.cmd == "reply-resolve":
        result = reply_and_resolve(args.thread, args.message, resolve=not args.no_resolve)
        print(json.dumps(result))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
