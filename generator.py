import random
import traceback

import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
from xvfbwrapper import Xvfb
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re
import os
import time
import shutil
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import XSD
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery
import glob
from openai import OpenAI

client = OpenAI(
    base_url="http://TODO",
    api_key="TODO",
)
model_name = "TODO"

def get_pages_from_category(category, shuffle=True):
    all_pages = []

    wiki_base_url = "https://en.wikipedia.org/wiki/"

    wiki_api_url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": "max",
        "cmtype": "page",
        "format": "json"
    }

    while True:
        response = requests.get(url=wiki_api_url, params=params)
        data = response.json()

        pages = data['query']['categorymembers']

        all_pages.extend(pages)

        if 'continue' not in data:
            break

        for k,v in data['continue'].items():
            params[k] = v

    if shuffle:
        random.shuffle(all_pages)
    else:
        all_pages.sort(key=lambda x: x['pageid'])

    return all_pages

def get_plaintext(pageid):
    wiki_api_url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "pageids": pageid
    }

    response = requests.get(url=wiki_api_url, params=params)
    data = response.json()

    plain_text = data['query']['pages'][str(params['pageids'])]['extract']

    return plain_text

def get_abstract(pageid):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "pageids": pageid,
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        if str(pageid) in pages:
            return pages[str(pageid)].get("extract")
        else:
            return None
    else:
        return None


def post_conversation(prompt):
    return client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    ).choices[0].message.content


def prompt_image_captions(plaintext):
    part = "about the mentioned video game in one sentences like an image caption solely based on the text above."
    prompts = [
        ("gameplay", f"Output an interesting and true gameplay fact {part}. Just output the gameplay fact."),
        ("story", f"Output an interesting and true game story detail {part}. Just output the story detail."),
        ("fun_fact", f"Output a true fun fact {part}. Just output the fact."),
        ("did_you_know", f"Output a \"Did you know\"-sentence {part}. Start with \"Did you know\"."),
        ("awkward_detail", f"Output a true but awkward detail {part}. Just output the detail."),
        ("trivia", f"Output an interesting and true trivia {part}. Just output the trivia.")
    ]

    results = {}
    for key, prompt in prompts:
        results[key] = post_conversation(plaintext + "\n\n" + prompt)
        results[key] = results[key].strip("'\" ")

    return results

def prompt_genre(plaintext):
    prompt = "Extract the genre of the video game. Only output the genre without any explanation."
    genre = post_conversation(plaintext + "\n\n" + prompt).strip("'\" ")
    return genre

def prompt_year(plaintext):
    prompt = "Extract the year in which the video game was released. Only output the year without any explanation."
    year = post_conversation(plaintext + "\n\n" + prompt).strip("'\" ")
    return year

def prompt_platforms(plaintext):
    prompt = "Extract a list of platforms on which the video game is released. Only output the platforms without any explanation."
    platforms = post_conversation(plaintext + "\n\n" + prompt).strip("'\" ")
    return platforms

def query_dbpedia_link(pageid):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    query = f"""
    SELECT ?res
    WHERE {{
      ?res dbo:wikiPageID {pageid}.
    }}
    LIMIT 1
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        res = result["res"]["value"]
        return res

    return None

def get_dbpedia_turtle(dbpedia_resource):
    name = dbpedia_resource.split('/')[-1]
    ttl_link = f"https://dbpedia.org/data/{name}.ttl"
    response = requests.get(ttl_link)
    ttl = response.content.decode("utf-8")
    return {
        "name": name,
        "ttl_link": ttl_link,
        "ttl": ttl
    }

def extract_from_ttl(resource_uri, ttl):
    graph = Graph()
    try:
        graph.parse(data=ttl, format="turtle")
    except:
        return {}

    dbo = Namespace("http://dbpedia.org/ontology/")
    dbp = Namespace("http://dbpedia.org/property/")

    queries = [
        ("dbp_genre",
        """
        SELECT DISTINCT ?value
        WHERE {
            ?resource (dbo:genre|dbp:genre) ?value .
        }
        """),
        ("dbp_year",
        """
        SELECT DISTINCT ?value
        WHERE {
            ?resource (dbo:releaseDate|dbp:released) ?value .
            FILTER(datatype(?value) = xsd:date || datatype(?value) = xsd:integer)
        }
        """),
        (
        "dbp_platform",
        """
        SELECT DISTINCT ?value
        WHERE {
            ?resource (dbp:platforms|dbo:computingPlatform) ?value .
        }
        """)
    ]

    ret = {}
    for key, query in queries:
        prep_query = prepareQuery(query, initNs={"dbo": dbo, "dbp": dbp, "xsd": XSD})

        results = graph.query(prep_query, initBindings={'resource': URIRef(resource_uri)})

        ret[key] = []
        for row in results:
            ret[key].append(row["value"])

    graph.close()
    return ret

def image_search(metadata, path):
    query = []
    title = metadata["title"]

    match = None
    if "prompt_year" in metadata:
        prompt_year = metadata["prompt_year"]
        match = re.search(r'\b\d{4}\b', prompt_year)

    query.append(title)
    if match:
        metadata["extract_year"] = int(match.group())
        query.append('(' + match.group() + ')')
    query.append("screenshots")

    return google_image_search_xvfb(" ".join(query), path)

def google_image_search_xvfb(query, path):
    wait_sec = 10
    try_count = 3

    image_tags = []
    while True:

        xvfb = Xvfb(width=1280, height=720)
        xvfb.start()
        browser = webdriver.Firefox()

        browser.get(f'https://www.google.de/search?q={urllib.parse.quote(query)}&udm=2')

        html = str(browser.page_source)

        soup = BeautifulSoup(html, 'html.parser')
        image_tags = soup.find_all("g-img")

        if len(image_tags) == 0:
            browser.quit()
            xvfb.stop()

            try_count -= 1
            if try_count == -1:
                return False

            print(f"{len(image_tags)} images found, waiting {wait_sec} seconds (try: {try_count}) ...")
            time.sleep(wait_sec)
        else:
            print(f"{len(image_tags)} images found")
            break

    for i, gimg in enumerate(image_tags):
        img = gimg.find('img')

        src = img['src']
        alt = img['alt']

        if not src.startswith("data"):
            continue

        name = f'{i:03}_img'
        if alt is not None and len(alt.strip()) != 0:
            name = f'{i:03}_{get_valid_filename(alt)}'

        ext = "png"
        if src.startswith("data:image/jpeg"):
            ext = 'jpg'
        elif src.startswith("data:image/gif"):
            ext = 'gif'

        response = urllib.request.urlopen(src)
        fullpath = path + '/' + name + '.' + ext
        try:
            with open(fullpath, 'wb') as f:
                f.write(response.file.read())

            # remove small images
            img_file = Image.open(fullpath)
            if img_file.width < 100:
                img_file.close()
                os.remove(fullpath)
        except:
            pass

    browser.quit()
    xvfb.stop()
    return True

def create_memes(game_folder_path, grid_x=2, grid_y=2, border_top_bottom=50, select_img_num=15, textwrap_width=50):
    font_path = "impact.ttf"

    # metadata
    with open(f'{game_folder_path}/metadata.json', 'r') as file:
        metadata = json.load(file)
    prompt_captions = metadata['prompt_captions']

    # load images
    img_paths = list_images_sorted(game_folder_path)
    imgs = []
    for img_path in img_paths:
        try:
            imgs.append(Image.open(img_path))
        except:
            pass

    max_width = max(imgs, key=lambda x: x.width).width
    max_height = max(imgs, key=lambda x: x.height).height

    full_width = 1500 # grid_x * max_width
    full_height = 1500 # grid_y * max_height

    for key,caption in prompt_captions.items():
        # will be cropped later
        meme_img = Image.new('RGB', (full_width, full_height))

        # randomize
        first_imgs = imgs[:select_img_num]
        random.shuffle(first_imgs)

        # build the meme based on images
        x = 0
        y = border_top_bottom
        max_y = 0
        bb_x = 0
        bb_y = 0
        for i, img in enumerate(first_imgs):

            if grid_x == 1:
                img = img.resize((img.width * 2, img.height * 2))

            use_width = img.width
            use_height = img.height

            meme_img.paste(img, (x, y))

            bb_x = max(bb_x, x + use_width)
            bb_y = max(bb_y, y + use_height)

            x += img.width
            max_y = max(max_y, use_height)

            # new line
            if (i+1) % grid_x == 0:
                x = 0
                y += max_y
                max_y = 0

            # end
            if (i+1) == grid_x * grid_y:
                break

        # crop it
        meme_img = meme_img.crop((0, 0, bb_x, bb_y + border_top_bottom))

        lines = textwrap.wrap(caption, textwrap_width, break_long_words=False)
        max_line = max(lines, key=len)

        meme_img_cpy = meme_img.copy()

        max_font_size = 30
        font_size = 4
        font = ImageFont.truetype(font_path, size=font_size) # ImageFont.load_default(font_size)
        while font.getbbox(max_line)[2] < (0.9 * meme_img_cpy.width):
            font_size += 1
            font = ImageFont.truetype(font_path, size=font_size) # ImageFont.load_default(font_size)
            if font_size >= max_font_size:
                break

        draw = ImageDraw.Draw(meme_img_cpy)

        if grid_x == 1 and grid_y == 3:
            line_switch_index = len(lines) + 1
        else:
            line_switch_index = int(round((len(lines) / 2))) - 1

        text_x, text_y, text_width, text_height = draw.textbbox([0, 0], max_line, font=font)
        text_y = 5

        border = 1

        for i, line in enumerate(lines):
            text = line

            text_x, _, text_width, text_height = draw.textbbox([0, 0], text, font=font)
            text_x = (meme_img_cpy.width - text_width) / 2

            draw.text((text_x - border, text_y - border), text, font=font, fill="black")
            draw.text((text_x + border, text_y - border), text, font=font, fill="black")
            draw.text((text_x - border, text_y + border), text, font=font, fill="black")
            draw.text((text_x + border, text_y + border), text, font=font, fill="black")

            draw.text((text_x, text_y), text, fill="white", font=font)

            text_y += text_height

            if i == line_switch_index:
                text_y = meme_img_cpy.height - (text_height * (len(lines) - line_switch_index - 1)) - 5

        meme_img_cpy.save(f'{game_folder_path}/meme-{key}-{grid_x}x{grid_y}.jpg')
        meme_img_cpy.close()

    meme_img.close()

    # close all
    for img in imgs:
        img.close()

def list_images_sorted(folder_path):
    all_files = []
    for ext in ['jpg', 'png']:
        all_files.extend(glob.glob(os.path.join(folder_path, '*.' + ext)))

    all_files = [f for f in all_files if re.match(r'^\d{3}', os.path.basename(f))]

    all_files_sorted = sorted(all_files)
    return all_files_sorted

def get_valid_filename(name):
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise Exception("Could not derive file name from '%s'" % name)
    return s

def download_pipeline(category, wait_sec=6):
    pages = get_pages_from_category(category, shuffle=False)
    print(f"{len(pages)} pages found in {category}")

    dir = 'GAMED'

    for page in pages:

        start_time = time.time()

        title = page["title"]
        pageid = page["pageid"]
        page_dir = str(page["pageid"])
        path = f"{dir}/{page_dir}"
        error_path = f"{dir}/01_error/{page_dir}"
        no_imgs_path = f"{dir}/00_no_imgs/{page_dir}"

        if os.path.exists(path) or os.path.exists(error_path) or os.path.exists(no_imgs_path):
            print(page_dir + " exists, skip")
            continue

        os.makedirs(path, exist_ok=True)
        print(title, pageid)

        try:
            metadata = {"title": title, "pageid": pageid, "category": category}

            print('query dbpedia')
            dbpedia_res = query_dbpedia_link(pageid)
            if dbpedia_res is not None:
                metadata["dbpedia_resource"] = dbpedia_res
                metadata.update(get_dbpedia_turtle(dbpedia_res))
                metadata.update(extract_from_ttl(metadata["dbpedia_resource"], metadata["ttl"]))

            print('query wikipedia')
            abstract = get_abstract(pageid)
            metadata["abstract"] = abstract

            plaintext = get_plaintext(pageid)
            metadata["plaintext"] = plaintext

            print('prompting')

            if len(abstract.strip()) != 0:
                genre = prompt_genre(abstract)
                metadata["prompt_genre"] = genre

                year = prompt_year(abstract)
                metadata["prompt_year"] = year

                platforms = prompt_platforms(abstract)
                metadata["prompt_platforms"] = platforms

            if len(plaintext.strip()) != 0:
                captions = prompt_image_captions(plaintext)
                metadata["prompt_captions"] = captions

            print("downloading images")
            success = image_search(metadata, path)

            # save metadata
            with open(f'{path}/metadata.json', 'w') as file: json.dump(metadata, file, indent=4)

            if success:
                print('create memes')
                create_memes(path, grid_x=1, grid_y=1, border_top_bottom=20, select_img_num=8, textwrap_width=50)
                create_memes(path, grid_x=1, grid_y=2, border_top_bottom=20, select_img_num=10, textwrap_width=50)
                create_memes(path, grid_x=1, grid_y=3, border_top_bottom=20, select_img_num=10, textwrap_width=50)
                create_memes(path, grid_x=2, grid_y=2, border_top_bottom=50, select_img_num=15, textwrap_width=50)
                create_memes(path, grid_x=2, grid_y=3, border_top_bottom=50, select_img_num=20, textwrap_width=50)

            if not success:
                no_imgs_dir = dir + "/00_no_imgs"
                os.makedirs(no_imgs_dir, exist_ok=True)
                shutil.move(path, no_imgs_dir)

        except:
            print(f'ERROR: move folder {path} to error dir')

            with open(path + '/stacktrace.txt', 'w') as f:
                f.write(traceback.format_exc())

            error_dir = dir + "/01_error"
            os.makedirs(error_dir, exist_ok=True)
            shutil.move(path, error_dir)


        wait = wait_sec
        print(f'done, waiting {wait} seconds ...')
        time.sleep(wait)

        end_time = time.time()
        duration = end_time - start_time
        print(f"Took {duration:.6f} seconds to complete")
