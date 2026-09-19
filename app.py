import streamlit as st
import pandas as pd
from pathlib import Path

# Configure the browser tab and page layout.
st.set_page_config(
    page_title="MLB Player Explorer",
    layout="wide" 
)

st.title("⚾ 2026 MLB Player Explorer")

st.write(
    "Compare MLB players using batting and pitching statistics. "
    "Use the sidebar to filter by team, position, and playing time."
)
# Subheader

st.sidebar.header("Filter players")
st.sidebar.write("Choose statistics, then narrow your results.")
 


# Choose which statistics to explore.
stat_type = st.selectbox(
    "Choose statistics",
    options=["Batting", "Pitching"]
)

# Select the corresponding CSV.
if stat_type == "Batting":
    filename = "mlb_batting_2026.csv"
else:
    filename = "mlb_pitching_2026.csv"

data_path = Path(__file__).parent / filename

# Keep baseball innings notation as text when loading pitching data.
if stat_type == "Pitching":
    df = pd.read_csv(data_path, dtype={"IP": str})
else:
    df = pd.read_csv(data_path)

# Read the CSV into a pandas DataFrame.
df = pd.read_csv(data_path)

# Convert position text into a list for each player.
position_lists = df["Positions"].fillna("").str.split(", ")

# Collect each distinct position and sort the options.
positions = sorted({
    position
    for player_positions in position_lists
    for position in player_positions
    if position
})

# Collect team names, remove duplicates, and sort alphabetically.
teams = sorted(df["Team"].dropna().unique())

# Add an option for viewing everyone.
team_options = ["All teams"] + teams

# Display a dropdown and store the user's selection.
selected_team = st.selectbox(
    "Choose a team",
    options=team_options,
    help="Select a team to view its players, or choose All teams."
)

# Decide which rows to display.
if selected_team == "All teams":
    filtered_df = df
else:
    filtered_df = df[df["Team"] == selected_team]

# Let the user select a position.
selected_position = st.selectbox(
    "Choose a position",
    options=["All positions"] + positions,
    help="Players appear under every position they played this season."
)

# Keep players whose position list contains the selection.
if selected_position != "All positions":
    matches_position = filtered_df["Positions"].fillna("").apply(
        lambda value: selected_position in value.split(", ")
    )

    filtered_df = filtered_df[matches_position]

if stat_type == "Batting":
    min_pa = st.slider(
        "Minimum plate appearances",
        min_value=0,
        max_value=max(1, int(df["PA"].max())),
        value=0
    )

   

    filtered_df = filtered_df[
        (filtered_df["PA"] >= min_pa)
        
    ]

else:
    min_innings = st.slider(
        "Minimum innings pitched",
        min_value=0,
        max_value=max(1, int(df["Outs"].max() // 3)),
        value=0,
        help="Show pitchers with at least this many complete innings."
    )

    # Three outs equal one inning.
    filtered_df = filtered_df[
        filtered_df["Outs"] >= min_innings * 3
    ]



st.subheader(f"{stat_type} results")
st.caption(f"{len(filtered_df)} player records match your filters.")

if filtered_df.empty:
    st.info("No players match. Try another team or lower the minimums.")
else:
    # Hide internal identifiers from the displayed table.
    display_df = filtered_df.drop(
        columns=["PlayerID", "Outs"],
        errors="ignore"
    )
    st.caption(
        "Click a column header to sort, view column statistics, "
        "resize, pin, or hide a column. "
        "Sort descending for the most home runs or strikeouts; "
        "sort ascending for the lowest ERA or WHIP."
    )
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )
