#!/usr/bin/python3

import json
import os
from pathlib import Path
import requests

TEXT_ENCODING = "utf-8"


def read_text(path):
    return Path(path).read_text(encoding=TEXT_ENCODING)


def write_text(path, content):
    Path(path).write_text(content, encoding=TEXT_ENCODING)


def read_json(path):
    return json.loads(read_text(path))


def write_json(path, data, compact=False, indent=None):
    kwargs: dict = {"ensure_ascii": False}
    if compact:
        kwargs["separators"] = (",", ":")
    elif indent is not None:
        kwargs["indent"] = indent
    Path(path).write_text(json.dumps(data, **kwargs), encoding=TEXT_ENCODING)


def load_cfg(path):
    cfg = {}
    with open(path, "r", encoding=TEXT_ENCODING) as myfile:
        for line in myfile:
            line = line.strip()
            if not line.startswith("#"):
                name, var = line.partition("=")[::2]
                cfg[name.strip()] = str(var.strip())
    return cfg


def sanitize_filename_component(value):
    invalid_filename_chars = '/\\<>:"|?*'
    invalid_filename_chars += "".join(chr(i) for i in range(32))
    table = str.maketrans("", "", invalid_filename_chars)
    sanitized = os.path.basename(value.replace("\\", "/")).translate(table).strip()
    return sanitized


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def build_request_headers(cfg, version):
    world_name = cfg["world_name"]
    return {
        "Content-Type": "application/json",
        "x-auth-token": cfg["x_auth_token"],
        "x-application-key": cfg["x_application_key"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " + version,
        "Referer": "https://www.worldanvil.com/w/" + world_name,
    }


def build_api_url(cfg):
    proxy_url = cfg.get("proxy", "")
    base_url = proxy_url if proxy_url != "" else "https://www.worldanvil.com"
    return base_url + "/api/external/boromir/"


def fetch_article_list_page(session, api_url, world_id, request_headers, limit=50, offset=0):
    endpoint = api_url + "world/articles?id=" + world_id + "&granularity=1"
    payload = {"limit": limit, "offset": offset}
    response = session.post(endpoint, json=payload, headers=request_headers)
    response.raise_for_status()
    return response.json()


def fetch_article(session, api_url, article_id, request_headers, granularity=3):
    endpoint = api_url + "article?id=" + article_id + "&granularity=" + str(granularity)
    response = session.get(endpoint, headers=request_headers)
    response.raise_for_status()
    return response.json()


def patch_article(session, api_url, article_id, payload, request_headers, timeout=60):
    endpoint = api_url + "article?id=" + article_id
    response = session.patch(
        endpoint, json=payload, headers=request_headers, timeout=timeout
    )
    response.raise_for_status()
    return response
