#!/usr/bin/python3

version = 'Tillerz Article Extract (v1.1)'

# --- requirements ----------------------------------------------------
# see https://github.com/Tillerz/worldanvil-templates/blob/master/tools/backup/

from argparse import ArgumentParser
from bs4 import BeautifulSoup
import datetime
import json
import os
from pathlib import Path
import requests
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
from sys import platform
import yaml

types_str = { "excerpt", "publicationDate", "notificationDate", "updateDate", "snippet", "scrapbook", "url", "name", "title", "slug", "state", "icon", "tags", "credits", "editURL", "metaTitle", "metaDescription", "metaKeywords", "canonicalURL", "robots", "ogTitle", "ogDescription", "ogImage", "twitterTitle", "twitterDescription", "twitterImage", "customCss", "customJs", "content", "sidepanelcontenttop", "sidepanelcontent", "sidebarcontent", "sidebarcontentbottom", "footnotes", "fullfooter", "subheading", "authornotes", "pronunciation" }
types_uuid = { "id", "worldID", "parentID", "categoryID", "authorID", "folderId" }
types_int = { "likes", "views", "wordcount", "viewCount", "likeCount", "commentCount", "positionX", "positionY", "zoomLevel", "mapWidth", "mapHeight", "mapMarkerWidth", "mapMarkerHeight" }
types_bool = { "isWip", "isDraft", "isAdultContent", "isLocked", "allowComments", "showAuthor", "showLastModified", "showWordCount", "showInSidebar", "showInMap", "isPinned", "isFeatured", "isFeaturedArticle", "isPublished", "showInToc", "isEmphasized", "displayAuthor", "displayChildrenUnder", "displayTitle", "displaySheet", "isEditable", "coverIsMap" }
default_fields = { "excerpt", "displayCss", "content", "pronunciation", "snippet", "sidebarcontent", "sidepanelcontenttop", "sidepanelcontent", "sidebarcontentbottom", "footnotes", "fullfooter", "authornotes", "scrapbook", "credits", "subheading" }

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
parser.add_argument('filename', help="article json file name, it will be looked for in the world/json folder")
parser.add_argument("-f", "--fields", required=False, help="fields to extract, separated by commas, default: " + ",".join(str(x) for x in default_fields))
parser.add_argument("-l", "--list", required=False, action='store_true', help="list fields found in the json file, default: only strings")
parser.add_argument("-a", "--all", required=False, action='store_true', help="-l will list ALL fields found in the json file, not just strings")
parser.add_argument("-t", "--types", required=False, action='store_true', help="-l will display the type of each field found")
parser.add_argument("-e", "--empty", required=False, action='store_true', help="create files for empty fields, too")
args = parser.parse_args()

os.chdir(os.path.dirname(__file__))

file_settings = "settings.cfg"

# read the config file
cfg = {}
try:
    with open(file_settings, "r") as myfile:
        for line in myfile:
            line = line.strip()
            if not line.startswith("#"):
                name, var = line.partition("=")[::2]
                cfg[name.strip()] = str(var.strip())
except FileNotFoundError:
    print(f"Error: The file {file_settings} was not found.")
    raise SystemExit(1)
except IOError:
    print(f"Error: The file {file_settings} could not be read.")
    raise SystemExit(1)

world_name = cfg['world_name']
world_id = cfg['world_id']
json_folder = world_name + "/json"
output_folder = world_name + "/edit"

# create the extract folder if it doesn't exist
try:
    os.makedirs(output_folder, exist_ok=True)
except OSError as error:
    print(f"Cannot create folder {output_folder}: {error}")
    raise SystemExit(1)

# --- action starts here ---------------------------------------------------

file_input = json_folder + '/' + args.filename
if os.path.isfile(file_input):
    jdata = json.loads(Path(file_input).read_text())

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
        print(f'Field list: ' + ",".join(str(x) for x in default_fields))
        print('------------------------')

        extract_folder = output_folder + '/' + slug

        # create the extract folder if it doesn't exist
        try:
            os.makedirs(extract_folder, exist_ok=True)
        except OSError as error:
            print(f"Cannot create folder {extract_folder}: {error}")
            raise SystemExit(1)

        # extract all the fields into single text files
        # if -e was given, create empty files for empty fields, too
        for field in fields:
            if field in jdata:
                file_for_field = extract_folder + '/' + field + ".txt"
                if (jdata[field] != "" and jdata[field] != None):
                    print(f'Extracting field {field} to {file_for_field}')
                    Path(file_for_field).write_text(jdata[field])
                else:
                    if args.empty:
                        Path(file_for_field).write_text("")
                    else:
                        print(f'Field {field} is empty/unset, not saving.')
            else:
                print(f'Field {field} not found in json data.')
        print('------------------------')

else:
    print(f"Could not find file {file_input}")
