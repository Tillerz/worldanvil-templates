# World Anvil Backup/Edit/Deploy Scripts

Scripts in this folder support a full flow:

1. download article JSON backups
2. extract editable text fields into plain text files
3. prepare minimal update payloads from edited text files
4. deploy payloads to WA REST API


# Requirements

- Python 3
- Python packages:
  - `requests`
  - `beautifulsoup4`
  - `lxml`

Install example:

```bash
pip install requests beautifulsoup4 lxml
```


# Configuration

Copy `settings-template.cfg` to `settings.cfg` and fill values:

- `world_name`
- `world_id`
- `x_auth_token`
- `x_application_key`
- `proxy` (optional; leave empty to use `https://www.worldanvil.com`)

The scripts read `settings.cfg` from this folder (`tools/backup`).


# Scripts

## 1) Full Backup

Script:

- Linux/macOS: `python3 backup-full.py`
- Windows: `backup-full.cmd`

Purpose:

- fetches all articles via WA API
- stores full article JSON in `<world_name>/json/`

Parameters:

- none


## 2) Extract Editable Fields

Script:

- Linux/macOS: `python3 extract.py <filename> [options]`
- Windows: `extract.cmd <filename> [options]`

Input:

- `<filename>` is a JSON file name from `<world_name>/json/`

Output:

- creates/updates `<world_name>/edit/<article-slug>/`
- writes one `<field>.txt` per extracted field
- writes `.jsonfile` with original JSON file name
- writes `.uuid` with article id (if present)

Usage:

```bash
usage: extract.py [-h] [-f FIELDS] [-l] [-a] [-t] [-e] filename
```

Parameters:

- `filename` article json file name, looked up in `<world_name>/json/`
- `-f, --fields` comma-separated field list to extract
- `-l, --list` list fields in JSON (default list mode: string fields)
- `-a, --all` with `-l`, include all fields (not only strings)
- `-t, --types` with `-l`, show field types
- `-e, --empty` create files for empty fields too


## 3) Prepare Deploy Payload for One Article

Script:

- Linux/macOS: `python3 prepare.py <article-slug>`
- Windows: `prepare.cmd <article-slug>`

Purpose:

- reads edited files from `<world_name>/edit/<article-slug>/`
- loads original JSON (`.jsonfile` marker, with fallback by slug)
- compares each edited field with original value
- creates minimal payload containing:
  - `id`
  - only changed fields
- writes payload to `<world_name>/deploy/<article-slug>.json`

Notes:

- `None` vs empty string for text fields is treated as unchanged
- prints byte/word diffs for changed fields listed in `word_count_fields`

Usage:

```bash
usage: prepare.py [-h] article_slug
```

Parameters:

- `article_slug` slug folder name under `<world_name>/edit/`


## 4) Deploy Payloads

Script:

- Linux/macOS: `python3 deploy.py [--dry-run] [--validate]`
- Windows: `deploy.cmd [--dry-run] [--validate]`

Purpose:

- scans `<world_name>/deploy/*.json`
- validates payload format (`id` + at least one changed field)
- sends updates to WA API:
  - method: `PATCH`
  - URL: `.../api/external/boromir/article?id=<article_id>`
  - body: payload without `id`

Usage:

```bash
usage: deploy.py [-h] [--dry-run] [--validate]
```

Parameters:

- `--dry-run` validate and print planned PATCH calls without sending requests
- `--validate` after successful PATCH, fetch article again and verify uploaded fields


# Typical Workflow

1. `python3 backup-full.py`
2. `python3 extract.py <article-json-file>`
3. edit files in `<world_name>/edit/<article-slug>/`
4. `python3 prepare.py <article-slug>`
5. review `<world_name>/deploy/<article-slug>.json`
6. `python3 deploy.py --dry-run`
7. `python3 deploy.py`
