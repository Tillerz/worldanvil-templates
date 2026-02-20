#!/usr/bin/python3
version = 'Tillerz Full Article Backup (v1.1)'

# --- requirements ----------------------------------------------------
# see https://github.com/Tillerz/worldanvil-templates/blob/master/tools/backup/

from bs4 import BeautifulSoup
from collections import deque
import json
import os
from pathlib import Path
import requests
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
from sys import platform
import time

os.chdir(os.path.dirname(__file__))

TEXT_ENCODING = "utf-8"

def read_text(path):
    return Path(path).read_text(encoding=TEXT_ENCODING)


def write_json(path, data, compact=False):
    kwargs: dict = {"ensure_ascii": False}
    if compact:
        kwargs["separators"] = (",", ":")
    Path(path).write_text(json.dumps(data, **kwargs), encoding=TEXT_ENCODING)

file_settings = "settings.cfg"
file_cookies = "cookies.json"

# read the config file
cfg = {}
try:
    with open(file_settings, "r", encoding=TEXT_ENCODING) as myfile:
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
proxy_url = cfg['proxy']

# headers for the rss request
request_headers =  {
    'Content-Type' : 'application/json',
    'x-auth-token' : cfg['x_auth_token'],
    'x-application-key' : cfg['x_application_key'],
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' + version,
    'Referer' : 'https://www.worldanvil.com/w/' + world_name
}

# api and rss urls:
base_url = "https://www.worldanvil.com"
if proxy_url != "":
    base_url = proxy_url

api_url = base_url + '/api/external/boromir/'

# this is the root folder for the backup:
root_folder = world_name
root_folder_json = root_folder + '/json'
file_all_articles_new = root_folder + "/all_articles_new.json"
file_all_articles_old = root_folder + "/all_articles_old.json"
file_all_articles = root_folder + "/all_articles.json"

# create a backup folder if it doesn't exist
try:
    os.makedirs(world_name, exist_ok=True)
except OSError as error:
    print(f"Cannot create folder {world_name}: {error}")
    raise SystemExit(1)

# --- action starts here ---------------------------------------------------

# create a session
with requests.Session() as session:
    if os.path.isfile(file_cookies):
        # load the saved cookies
        cookies = json.loads(read_text(file_cookies))
        # turn the object into a a cookie jar
        cookies = cookiejar_from_dict(cookies)
        # attach cookies to session
        session.cookies.update(cookies)

    # global timer
    loop_start = time.monotonic()

    # read article list
    pagesize = 50
    all_articles_new = []
    try:
        offset = 0
        request_times = deque(maxlen=5)
        # fetch <pagesize> article, add them to the list and then increase offset for next <pagesize> articles
        counter = 0
        while True:
            if len(request_times) == request_times.maxlen:
                elapsed = time.monotonic() - request_times[0]
                if elapsed < 5:
                    time.sleep(5 - elapsed)
            request_times.append(time.monotonic())
            get_article_list = api_url + "world/articles?id=" + world_id + "&granularity=1"
            payload = { 'limit': pagesize, 'offset' : offset }
            response = session.post(get_article_list, json=payload, headers=request_headers)
            response.raise_for_status()
            jdata = response.json()
            if jdata.get("success") is True:
                if jdata.get("entities") == []:
                    break
                else:
                    all_articles_new.extend(jdata.get("entities", []))
                    offset += pagesize
                    counter += 1
                    print(f"{counter * pagesize} articles read (article list)")
                    # debug: print(json.dumps(jdata))
            else:
                break
    except requests.RequestException as e:
        print(f"Error fetching article list: {e}")
        raise SystemExit(1)

    if not all_articles_new:
        print("Error: No articles returned from API.")
        raise SystemExit(1)

    print("Comparing list of existing articles with downloaded list.")
    # load old article list, if existing
    all_articles_path = Path("all_articles.json")
    if all_articles_path.exists():
        all_articles_old = json.loads(read_text(all_articles_path))
    else:
        all_articles_old = []

    write_json(file_all_articles_new, all_articles_new, compact=True)

    old_dates_by_id = {
        a.get("id"): a.get("updateDate", {}).get("date")
        for a in all_articles_old
        if "id" in a
    }
    new_articles = []
    for a in all_articles_new:
        article_id = a.get("id")
        if article_id is None:
            continue
        old_date = old_dates_by_id.get(article_id)
        new_date = a.get("updateDate", {}).get("date")
        if old_date is None or (new_date is not None and new_date > old_date):
            new_articles.append(article_id)

    # debug: Path("new_articles.json").write_text(json.dumps(new_articles, separators=(",", ":")))

    request_times = deque(maxlen=5)
    # loop over all new or changed articles
    remaining = len(new_articles)
    updated_count = 0
    unchanged_count = 0
    for article_id in new_articles:
        if len(request_times) == request_times.maxlen:
            elapsed = time.monotonic() - request_times[0]
            if elapsed < 5:
                time.sleep(5 - elapsed)
        request_times.append(time.monotonic())
        # fetch article via API with granularity 3, means full article with all fields
        get_article = api_url + "article?id=" + article_id + "&granularity=3"
        try:
            response = session.get(get_article, headers=request_headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article data: {e}")
            continue

        # parse the json file and extract some values
        jdata = response.json()
        length = len(json.dumps(jdata))
        length_old = 0

        slug = jdata["slug"]
        wordcount = jdata["wordcount"]
        last_modif = jdata["updateDate"]["date"]

        # build path + filename to save the json:
        file_json_article_base = root_folder_json + '/' + slug + '_' + last_modif.replace(".000000","").replace(' ','_').replace(':','')
        last_modif_old = ""
        old_wordcount = 0
        perc = 100
        wdiff = ""

        # if the file already exists, load it and extract some values for comparison with the new downloaded version
        if os.path.isfile(file_json_article_base + '.json'):
            oldfile = read_text(file_json_article_base + '.json')

            length_old = len(oldfile)
            olddata = json.loads(oldfile)
            old_wordcount = olddata["wordcount"]
            last_modif_old = olddata["updateDate"]["date"]

            if (old_wordcount > 0):
                perc = wordcount * 100 / old_wordcount

            if (old_wordcount > 0):
                diff = wordcount - old_wordcount
                if (diff >= 0):
                    wdiff = "+" + str(diff)
                wdiff = "("+str(wdiff)+", "+str(round(perc))+"% of previous size)"
        # do not save new article if it is unchanged
        if ((last_modif_old == last_modif) and (diff == 0) and (length == length_old)):
            print(f'SLUG: {slug} --> file did not change, not saving.')
            unchanged_count += 1
        else:
            # print some output for the user
            print(f'SLUG: {slug} ({article_id})')
            print(f'Last Modified: {last_modif.replace(".000000","")}')
            print(f'Wordcount: {wordcount} {wdiff}')

            # write the json file to disk
            print(f'Writing file to {file_json_article_base}.json')
            write_json(file_json_article_base + '.json', jdata)
            updated_count += 1

            # for debug: print(json.dumps(response.json(), indent=2))
        remaining -= 1
        print(f'------------------------ {remaining}')

    if updated_count == 0:
        print(f"{unchanged_count} articles were already up-to-date.")
        if os.path.isfile(file_all_articles_new):
            os.remove(file_all_articles_new)
    else:
        print(f"Updated {updated_count} articles, {unchanged_count} articles were already up-to-date.")
        if os.path.isfile(file_all_articles_old):
            os.remove(file_all_articles_old)
        if os.path.isfile(file_all_articles):
            os.replace(file_all_articles, file_all_articles_old)
        if os.path.isfile(file_all_articles_new):
            os.replace(file_all_articles_new, file_all_articles)

    elapsed = int(time.monotonic() - loop_start)
    minutes, seconds = divmod(elapsed, 60)
    print(f"Elapsed time: {minutes}m {seconds:02d}s")

    # turn cookiejar into dict and save it
    cookies = dict_from_cookiejar(session.cookies)
    if os.path.isfile(file_cookies):
        if session.cookies:
            cookies = dict_from_cookiejar(session.cookies)
        else:
            cookies = {}
    write_json(file_cookies, cookies)
