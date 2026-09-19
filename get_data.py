import json
from urllib.request import urlopen
from urllib.parse import urlencode
from pathlib import Path

import pandas as pd

SEASON = 2026
FOLDER = Path(__file__).parent


# 1. Create a reusable function for downloading MLB statistics.
def get_stats(group):
    records = []
    offset = 0

    # Download additional pages if the response has more records.
    while True:
        parameters = urlencode({
            "stats": "season",
            "group": group,
            "season": SEASON,
            "sportIds": 1,
            "playerPool": "ALL",
            "limit": 1000,
            "offset": offset,
        })

        url = f"https://statsapi.mlb.com/api/v1/stats?{parameters}"

        with urlopen(url, timeout=30) as response:
            data = json.load(response)

        result = data["stats"][0]
        batch = result["splits"]

        if not batch:
            break

        records.extend(batch)
        offset += len(batch)

        if offset >= result["totalSplits"]:
            break

    return records


# 2. Download the three groups of statistics.
print("Downloading batting statistics...")
batting_records = get_stats("hitting")

print("Downloading pitching statistics...")
pitching_records = get_stats("pitching")

print("Downloading positions played...")
fielding_records = get_stats("fielding")


# 3. Collect every position reported for each player.
positions_by_player = {}

for record in fielding_records:
    player_id = record["player"]["id"]
    position = record.get("position", {}).get("abbreviation")

    if position:
        positions_by_player.setdefault(player_id, set()).add(position)

# Anyone with pitching statistics should also have position P.
for record in pitching_records:
    player_id = record["player"]["id"]
    positions_by_player.setdefault(player_id, set()).add("P")


# 4. Create the identifying columns shared by both datasets.
def player_details(record):
    player_id = record["player"]["id"]
    positions = positions_by_player.get(player_id, set())

    return {
        "PlayerID": player_id,
        "Player": record["player"]["fullName"],
        "Team": record.get("team", {}).get("name", "Multiple teams"),
        "Positions": ", ".join(sorted(positions)) or "Unknown",
    }


# 5. Select batting statistics.
batting_columns = {
    "Games": "gamesPlayed",
    "PA": "plateAppearances",
    "HR": "homeRuns",
    "RBI": "rbi",
    "AVG": "avg",
    "OBP": "obp",
    "SLG": "slg",
    "OPS": "ops",
}

# Select pitching statistics.
pitching_columns = {
    "Games": "gamesPlayed",
    "GS": "gamesStarted",
    "W": "wins",
    "L": "losses",
    "SV": "saves",
    "IP": "inningsPitched",
    "Outs": "outs",
    "SO": "strikeOuts",
    "BB": "baseOnBalls",
    "ERA": "era",
    "WHIP": "whip",
}


# 6. Turn downloaded records into a table.
def build_table(records, columns):
    rows = []

    for record in records:
        row = player_details(record)

        for label, api_name in columns.items():
            row[label] = record["stat"].get(api_name)

        rows.append(row)

    df = pd.DataFrame(rows)

    for column in columns:
        # Innings pitched uses baseball notation, not decimal notation.
        if column != "IP":
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


batting_df = build_table(batting_records, batting_columns)
pitching_df = build_table(pitching_records, pitching_columns)


# 7. Save both datasets beside this script.
batting_df.to_csv(
    FOLDER / f"mlb_batting_{SEASON}.csv",
    index=False
)

pitching_df.to_csv(
    FOLDER / f"mlb_pitching_{SEASON}.csv",
    index=False
)

print(f"Saved {len(batting_df)} batting records.")
print(f"Saved {len(pitching_df)} pitching records.")

print(batting_df[["Player", "Positions"]].head())