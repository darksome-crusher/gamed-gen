from generator import *

for year in reversed(range(1980, 2025)):
    print(f"\n\n\nYEAR {year}\n")
    download_pipeline(f"Category:{year}_video_games")
