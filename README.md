# GAMED-Gen: A Fully Automatic Video Game Meme Generator

This code uses
* wikipedia to query video game pages,
* LLMs to prompt captions and
* Google image search to crawl screenshot images

to fully automatically generate video game memes.

<center>

![](img/meme-gameplay-1x1.jpg)

</center>

## Setup

```sh
pip install -r requirements.txt
```

Change settings in `generator.py` for LLM prompting.
```py
client = OpenAI(
    base_url="http://TODO",
    api_key="TODO",
)
model_name = "TODO"
```

## Run

In the main you can set what wikipedia categories are crawled.
```py
for year in reversed(range(1980, 2025)):
    print(f"\n\n\nYEAR {year}\n")
    download_pipeline(f"Category:{year}_video_games")
```

## Example

```
$ python main.py

YEAR 2024

134 pages found in Category:2024_video_games
Solium Infernum 18830587
query dbpedia
query wikipedia
prompting
downloading images
205 images found
create memes
done, waiting 6 seconds ...
```

In the `GAMED` folder a subfolder `18830587` is created with the following content.

```
metadata.json

meme-awkward_detail-1x1.jpg
meme-awkward_detail-1x2.jpg
meme-awkward_detail-1x3.jpg
meme-awkward_detail-2x2.jpg
meme-awkward_detail-2x3.jpg
meme-did_you_know-1x1.jpg
meme-did_you_know-1x2.jpg
meme-did_you_know-1x3.jpg
meme-did_you_know-2x2.jpg
meme-did_you_know-2x3.jpg
meme-fun_fact-1x1.jpg
meme-fun_fact-1x2.jpg
meme-fun_fact-1x3.jpg
meme-fun_fact-2x2.jpg
meme-fun_fact-2x3.jpg
meme-gameplay-1x1.jpg
meme-gameplay-1x2.jpg
meme-gameplay-1x3.jpg
meme-gameplay-2x2.jpg
meme-gameplay-2x3.jpg
meme-story-1x1.jpg
meme-story-1x2.jpg
meme-story-1x3.jpg
meme-story-2x2.jpg
meme-story-2x3.jpg
meme-trivia-1x1.jpg
meme-trivia-1x2.jpg
meme-trivia-1x3.jpg
meme-trivia-2x2.jpg
meme-trivia-2x3.jpg

005_Solium_Infernum_2009_-_release_date_videos_screenshots_reviews_on_RAWG.jpg
007_Unknown_Pleasures_2009_Solium_Infernum__Rock_Paper_Shotgun.jpg
009_Screenshot_of_Solium_Infernum_To_Reign_Is_Worth_Ambition_Windows_2009_-__MobyGames.jpg
011_Screenshot_of_Solium_Infernum_To_Reign_Is_Worth_Ambition_Windows_2009_-__MobyGames.jpg
013_Solium_Infernum_Is_a_Reimagining_of_a_2009_Strategy_Cult_Classic.jpg
015_Solium_Infernum_1.05_Screenshots_for_Windows_-_Download.io.jpg
(...)
```

The `metadata.json` file contains the following information.
```json
{
    "title": "Solium Infernum",
    "pageid": 18830587,
    "category": "Category:2024_video_games",
    "dbpedia_resource": "http://dbpedia.org/resource/Solium_Infernum",
    "name": "Solium_Infernum",
    "ttl_link": "https://dbpedia.org/data/Solium_Infernum.ttl",
    "ttl": "@prefix dbo:\t<http://dbpedia.org/ontology/> (...)",
    "dbp_genre": [
        "http://dbpedia.org/resource/Turn-based_strategy"
    ],
    "dbp_year": [
        "2009-11-26"
    ],
    "dbp_platform": [
        "http://dbpedia.org/resource/Microsoft_Windows"
    ],
    "abstract": "Solium Infernum is a turn-based strategy computer game for Windows from independent game developer Cryptic Comet, creator of Armageddon Empires, and was released on November 26, 2009. (...)",
    "plaintext": "Solium Infernum is a turn-based (...)\n\n\n== References ==\n\n\n== External links ==\nOfficial website (original)\nOfficial website (remake)",
    "prompt_genre": "Strategy",
    "prompt_year": "2009 (for the original release), 2024 (for the remake release)",
    "prompt_platforms": "Windows, PC (...)",
    "prompt_captions": {
        "gameplay": "In Solium Infernum, players compete as archfiends to secure the throne of Hell, engaging in both diplomacy and military tactics to raise their standing among rivals.",
        "story": "In Solium Infernum, players compete as archfiends vying for the throne of Hell, navigating diplomacy and military tactics to secure their position among rivals, with the game's AI filling in for missing players if necessary.",
        "fun_fact": "The remake version of Solium Infernum, originally developed by Cryptic Comet, was designed by game developer Anthony Sweet and released by League of Geeks on February 22, 2024, after several release date postponements.",
        "did_you_know": "Did you know? Solium Infernum, the turn-based strategy game, was met with critical acclaim despite receiving little attention from mainstream gaming press. The remake version, developed by League of Geeks, was highly anticipated, with its release date postponed multiple times before finally launching on February 22, 2024.",
        "awkward_detail": "Despite its initial release in 2009, the remake of Solium Infernum, a strategic game about battling for the throne of Hell, wasn't released until 2024.",
        "trivia": "The remake of Solium Infernum, a strategic game about vying for the throne of Hell, was developed by League of Geeks and was initially scheduled for release in 2023, but was eventually delayed and released on February 22, 2024, under the same name."
    },
    "extract_year": 2009
}
```
