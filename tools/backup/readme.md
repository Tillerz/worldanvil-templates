
# Backup Script for World Anvil articles based on the Recently Modified RSS list

Loads the Recent Articles RSS from World Anvil and downloads + saves the JSON file for each, if needed.

IMPORTANT NOTE: This will only find articles that are published and not hidden behind subscriber groups, because the 'Recent Articles' list only contains entries that are visible to everyone.

The script will create a folder <worldname> and put all the articles in there, naming them <slug>.json, where <slug> is the article SLUG used by WA. Optionally (default) you can have the `last modified` appended to the SLUG.


# Requirements

1. You need a python 3 installation and the xml libraries:

- install Python 3.x
- - Linux: execute `apt install python3`
- - Windows: get Python 3 installer here: `https://www.python.org/downloads/`

In a shell window (Linux, MacOS) or command prompt window (Windows):

- execute `pip install lxml` (xml parser)
- execute `pip install bs4` (html/xml -> data)

2. You need the script and the config file:

Option 1: get files via git

- install git client
- - Linux: execute `apt install git`
- - Windows: get the 64bit/Portable version from `https://www.git-scm.com/download/win` and install it
- execute `git clone https://github.com/Tillerz/worldanvil-templates/tree/master/tools/backup wa-backup`

Option 2: download files manually

- make a folder somewhere (eg `C:\wa-backup\` or `/home/username/wa-backup/`) and change into it
- save backup.cmd (only for Windows), backup.py and settings.cfg into this folder.

Afterwards the folder should look like this:

```bash
yourworldname/
backup.cmd
backup.py
settings.cfg
```

# Configuration

You need to adjust the values in `settings.cfg`:

```python
# world name, example: alana
world_name = YOUR_WORLD_NAME_HERE

# world id, example: b4c38990-f121-44b9-a966-2c80514ff3d6
# You find the id in the address bar of the browser after clicking 'Edit World'.
world_id = YOUR_WORLD_ID_HERE

# WA Authentication token, you can create on here: https://www.worldanvil.com/api/auth/key
x_auth_token = AUTH_TOKEN_HERE_THE_REALLY_REALLY_LONG_ONE

# WA application key, you request this one from Dimitris (WA)
x_application_key = APPLICATION_KEY_HERE

# if the new file is down to this percentage of the previous version, then do NOT overwrite but print an error.
# example: 75 = if the file is only 75% of its previous size (or smaller), do not overwrite
overwrite_threshold = 75

# True or False, default: True. If set to True, saved files will be named <slug>-<last_modif>.json, eg. martine-character-2024-06-05_143000.json
# That way you have a fresh copy with each edit.
append_last_modif = True

# use a cloudflare worker as a proxy inbetween
# Setup instructions see here: https://developers.cloudflare.com/learning-paths/workers/get-started/first-worker/
# proxy = https://YOURWORKER.NAME.workers.dev
proxy =
```

# Backup Script

## Windows

On Windows, just open the folder in Explorer and double-click backup.cmd

## Linux

On MacOS and Linux, open a bash window, change to the folder with the script and execute `python backup.py`

You can also add it to the crontab. Example (runs every 15 minutes, only from 9am to 8pm ):

`*/15 9-20 * * * cd /opt/wa-backup ; python ./backup.py > /opt/wa-backup/backup.log 2>&1`

Note: do not force spam requests to WA. That causes unneeded traffic on the systems and also might trigger a block by Cloudflare.

# Extract Script

Open a command prompt / bash and change to the folder with the scripts. The folder with your worldname should be visible in there, containing your backups.

## Windows

Execute the script `.\extract.cmd` with the parameters you need.

## Linux

Execute the script `./extract.py` with the parameters you need.

## Parameters

```bash
usage: extract.[py|cmd] [-h] [-f FIELDS] [-l] [-a] [-t] filename
positional arguments:
  filename              article json file name, it will be looked for in the world folder

options:
  -h, --help            show this help message and exit
  -f FIELDS, --fields FIELDS
                        fields to extract, separated by commas, default:
                        content,sidepanelcontenttop,sidepanelcontent,sidebarcontentbottom,footnotes,fullfooter,displayCss
  -l, --list            list fields found in the json file, default: only strings
  -a, --all             -l will now list ALL fields found in the json file
  -t, --types           -l will now display the type of each field found
```

Example: you want to extract the main content fields of an article:

`extract.py yourworldname\articlebackup.json`

This will extract the main fields (content, sidepanelcontenttop, sidepanelcontent, sidebarcontentbottom, footnotes, fullfooter, displayCss) into a sub folder `extract/` with the `article-slug` being the filename, followed by `_<fieldname>` and ending with `.txt`. The content of each file is plain text and ready for a copy/paste back into your WA article.

Example: you want to extract just the css or whichever two fields:

`extract.py yourworldname\articlebackup.json --fields displayCss`
`extract.py yourworldname\articlebackup.json --fields fieldname1,fieldname2`

List all the fieldnames of your article backup (just the text ones, no booleans etc):

`extract.py yourworldname\articlebackup.json -l`

If you want to get ALL fields, you use:

`extract.py yourworldname\articlebackup.json -l -a`

And if you also want to see the type of each field:

`extract.py yourworldname\articlebackup.json -l -a -t`
