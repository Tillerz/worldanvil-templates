#!/usr/bin/python3

version = 'Tillerz Article Extract (v1.0)'

from sys import platform
from bs4 import BeautifulSoup
from pathlib import Path
import requests
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
import json
import yaml
import datetime
import os
from argparse import ArgumentParser

default_fields = "content,sidepanelcontenttop,sidepanelcontent,sidebarcontentbottom,footnotes,fullfooter,displayCss"

parser = ArgumentParser()
parser.add_argument('filename', help="article json file name, it will be looked for in the world folder")
parser.add_argument("-f", "--fields", required=False, help="fields to extract, separated by commas, default: " + default_fields)
parser.add_argument("-l", "--list", required=False, action='store_true', help="list fields found in the json file, default: only strings")
parser.add_argument("-a", "--all", required=False, action='store_true', help="-l will now list ALL fields found in the json file")
parser.add_argument("-t", "--types", required=False, action='store_true', help="-l will now display the type of each field found")
args = parser.parse_args()

# --- requirements ----------------------------------------------------
# see https://github.com/Tillerz/worldanvil-templates/blob/master/tools/backup/

# VS Code (Windows) does not switch to the folder the script is in, so we need to do it ourselves
if platform in ('win32', 'cygwin'):
    os.chdir(os.path.dirname(__file__))

# read the config file
cfg = {}
try:
    with open("settings.cfg", "r") as myfile:
        for line in myfile:
            line = line.strip()
            if not line.startswith("#"):
                name, var = line.partition("=")[::2]
                cfg[name.strip()] = str(var.strip())
except FileNotFoundError:
    print("Error: The settings.cfg file was not found.")
    exit(1)
except IOError:
    print("Error: The settings.cfg file could not be read.")
    exit(1)
world_name = cfg['world_name']
world_id = cfg['world_id']
output_folder = "extract"

# create the extract folder if it doesn't exist
try:
    os.makedirs(output_folder, exist_ok=True)
except OSError as error:
    print(f"Cannot create folder {output_folder}: "+error)

# --- action starts here ---------------------------------------------------

inputfile = args.filename
if os.path.isfile(inputfile):
    # load the saved cookies
    jdata = json.loads(Path(inputfile).read_text())

    # print(json.dumps(jdata, indent=2))

    title = jdata["title"]
    slug = jdata["slug"]
    wordcount = jdata["wordcount"]
    last_modif = jdata["updateDate"]["date"]

    print(f'Title: {title}')
    print(f'Slug: {slug}')
    print(f'Last Modified: {last_modif.replace(".000000","")}')
    print(f'Wordcount: {wordcount} words')
    
    if (args.list or args.all):
        print('------------------------')
        print('Fields found in article json file:')
        print('------------------------')
        for field in jdata:
            if (jdata[field] != "" and jdata[field] != None):
                if (type(jdata[field]) == str or args.all):
                    if (args.types):
                        print(f'{field}\t\t{type(jdata[field])}')
                    else:
                        print(f'{field}')
            else:
                print(f'{field}')
        print('------------------------')
    else:
        fields = default_fields
        if (args.fields != None and args.fields != ""):
            fields = args.fields

        print(f'Field list: {fields}')
        fields = fields.split(",")
        print('------------------------')
        for field in fields:
            if field in jdata:
                if (jdata[field] != "" and jdata[field] != None):
                    fullpath = output_folder + "/" + slug + "_" + field + ".txt"
                    print(f'Extracting field {field} to {fullpath}')
                    Path(fullpath).write_text(jdata[field])
                else:
                    print(f'Field {field} is empty, not saving.')
            else:
                print(f'Field {field} not found in json data.')
        print('------------------------')
