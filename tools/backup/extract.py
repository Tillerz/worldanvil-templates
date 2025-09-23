#!/usr/bin/python3

version = 'Tillerz Article Extract (v1.1)'

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

types_str = { "excerpt", "publicationDate", "notificationDate", "updateDate", "snippet", "scrapbook", "url", "name", "title", "slug", "state", "icon", "tags", "credits", "editURL", "metaTitle", "metaDescription", "metaKeywords", "canonicalURL", "robots", "ogTitle", "ogDescription", "ogImage", "twitterTitle", "twitterDescription", "twitterImage", "customCss", "customJs", "content", "sidepanelcontenttop", "sidepanelcontent", "sidebarcontent", "sidebarcontentbottom", "footnotes", "fullfooter", "subheading", "authornotes", "pronunciation"}
types_uuid = { "id", "worldID", "parentID", "categoryID", "authorID", "folderId"}
types_int = { "likes", "views", "wordcount", "viewCount", "likeCount", "commentCount", "positionX", "positionY", "zoomLevel", "mapWidth", "mapHeight", "mapMarkerWidth", "mapMarkerHeight"}
types_bool = { "isWip", "isDraft", "isAdultContent", "isLocked", "allowComments", "showAuthor", "showLastModified", "showWordCount", "showInSidebar", "showInMap", "isPinned", "isFeatured", "isFeaturedArticle", "isPublished", "showInToc", "isEmphasized", "displayAuthor", "displayChildrenUnder", "displayTitle", "displaySheet", "isEditable", "coverIsMap" }
default_fields = { "content", "sidepanelcontenttop", "sidepanelcontent", "sidebarcontentbottom", "footnotes", "fullfooter", "displayCss" }

# --- unroll() ----------------------------------------------------

def unroll(data, indent=0, types=False, all=False, fields={}):
    spacing = "  " * (indent)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                if all or (fields != {} and key in fields):
                    print(f"{spacing}{key}:")
                unroll(value, indent + 1, types, all)
            else:
                if all or (fields != {} and key in fields):
                    o = "?" if type(value).__name__ == "NoneType" else type(value).__name__
                    if key in types_str:
                        o = "str"
                    if key in types_uuid:
                        o = "uuid"
                    if key in types_int:
                        o = "int"
                    if key in types_bool:
                        o = "bool"
                    if all or o == "str":
                        if types:
                            print(f"{spacing}{key}: {o}")
                        else:
                            print(f"{spacing}{key}: {value}")
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                if all or (fields != {} and item in fields):
                    print(f"{spacing}[{index}]")
                unroll(item, indent + 1, types, all)
            else:
                if all or (fields != {} and item in fields):
                    print(f"{spacing}- {item}")
    else:
        print(f"{spacing}{data}")

# --- main() ----------------------------------------------------

parser = ArgumentParser()
parser.add_argument('filename', help="article json file name, it will be looked for in the world folder")
parser.add_argument("-f", "--fields", required=False, help="fields to extract, separated by commas, default: " + " ".join(str(x) for x in default_fields))
parser.add_argument("-l", "--list", required=False, action='store_true', help="list fields found in the json file, default: only strings")
parser.add_argument("-a", "--all", required=False, action='store_true', help="-l will list ALL fields found in the json file, not just strings")
parser.add_argument("-t", "--types", required=False, action='store_true', help="-l will display the type of each field found")
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
    fields = default_fields
    if (args.fields != None and args.fields != ""):
        fields = args.fields.split(',')

    print(f'Title: {title}')
    print(f'Slug: {slug}')
    print(f'Last Modified: {last_modif.replace(".000000","")}')
    print(f'Wordcount: {wordcount} words')
    
    if (args.list):
        print('------------------------')
        print('Fields found in article json file:')
        print('------------------------')
        for field in jdata:
            unroll({field: jdata[field]}, 0, args.types, args.all, fields)
        print('------------------------')
    else:
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
