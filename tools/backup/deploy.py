#!/usr/bin/python3
version = "Tillerz Article Deploy"

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import requests
from wa_common import (
    build_api_url,
    build_request_headers,
    load_cfg,
    patch_article,
    read_json,
)

# main
os.chdir(os.path.dirname(__file__))

parser = ArgumentParser()
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="validate deploy payloads and print what would be sent, but do not PATCH",
)
args = parser.parse_args()

file_settings = "settings.cfg"
try:
    cfg = load_cfg(file_settings)
except FileNotFoundError:
    print(f"Error: The file {file_settings} was not found.")
    raise SystemExit(1)
except IOError:
    print(f"Error: The file {file_settings} could not be read.")
    raise SystemExit(1)

world_name = cfg["world_name"]
deploy_folder = Path(world_name) / "deploy"
if not deploy_folder.is_dir():
    print(f"Deploy folder not found: {deploy_folder.as_posix()}")
    raise SystemExit(1)

payload_files = sorted(deploy_folder.glob("*.json"))
if not payload_files:
    print(f"No deploy files found in {deploy_folder.as_posix()}")
    raise SystemExit(0)

api_url = build_api_url(cfg)
request_headers = build_request_headers(cfg, version)

print(f"Deploy folder: {deploy_folder.as_posix()}")
print(f"Deploy files found: {len(payload_files)}")
print(f"Mode: {'dry-run' if args.dry_run else 'live'}")

deployable_count = 0
deployed_count = 0
with requests.Session() as session:
    for file_path in payload_files:
        try:
            payload = read_json(file_path)
        except json.JSONDecodeError as error:
            print(f"Skipping {file_path.name}: invalid JSON ({error})")
            continue

        article_id = payload.get("id")
        if not article_id:
            print(f"Skipping {file_path.name}: missing required field 'id'")
            continue
        if len(payload.keys()) <= 1:
            print(f"Skipping {file_path.name}: no changed fields in payload")
            continue

        deployable_count += 1
        changed_fields = [key for key in payload.keys() if key != "id"]
        print(f"Prepared: {file_path.name} -> article {article_id}")
        print(f"Fields: {', '.join(changed_fields)}")

        update_article = api_url + "article?id=" + article_id
        update_payload = {key: value for key, value in payload.items() if key != "id"}
        if args.dry_run:
            print(f"Dry-run: PATCH {update_article}")
            continue

        try:
            patch_article(
                session,
                api_url,
                article_id,
                update_payload,
                request_headers,
                timeout=60,
            )
            deployed_count += 1
            print(f"Deployed: {file_path.name}")
        except requests.RequestException as error:
            print(f"Deploy failed for {file_path.name}: {error}")

print(f"Deployable payloads: {deployable_count}")
print(f"Deployed payloads: {deployed_count}")
