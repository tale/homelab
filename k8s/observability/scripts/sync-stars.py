import argparse
import base64
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def request(path, method="GET"):
    credentials = f"{os.environ['GRAFANA_USER']}:{os.environ['GRAFANA_PASSWORD']}"
    headers = {
        "Authorization": "Basic " + base64.b64encode(credentials.encode()).decode(),
        "X-Grafana-Org-Id": "1",
    }
    url = os.environ["GRAFANA_URL"].rstrip("/") + path
    with urlopen(Request(url, headers=headers, method=method), timeout=15) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dashboard_uids = set()
    page = 1
    while True:
        dashboards = request(f"/api/search?type=dash-db&tag=homelab&limit=1000&page={page}")
        dashboard_uids.update(dashboard["uid"] for dashboard in dashboards)
        if len(dashboards) < 1000:
            break
        page += 1

    if not dashboard_uids:
        raise SystemExit("No homelab dashboards found; waiting for dashboard provisioning")

    users = request("/api/org/users")
    user_count = 0
    added_count = 0
    for user in users:
        if user.get("isDisabled") or user.get("isServiceAccount"):
            continue

        user_count += 1
        path = "/apis/collections.grafana.app/v1alpha1/namespaces/default/stars/user-"
        path += quote(user["uid"], safe="")
        try:
            stars = request(path)
        except HTTPError as error:
            if error.code != 404:
                raise
            stars = {}

        existing_uids = {
            uid
            for resource in stars.get("spec", {}).get("resource", [])
            if resource["group"] == "dashboard.grafana.app" and resource["kind"] == "Dashboard"
            for uid in resource["names"]
        }
        for uid in sorted(dashboard_uids - existing_uids):
            if not args.dry_run:
                # Add individually so concurrent personal stars are preserved.
                request(path + "/update/dashboard.grafana.app/Dashboard/" + quote(uid, safe=""), "PUT")
            added_count += 1

    action = "Would add" if args.dry_run else "Added"
    print(f"{action} {added_count} stars for {user_count} users across {len(dashboard_uids)} dashboards")


if __name__ == "__main__":
    main()
