import nfl_data_py as nfl
import pandas as pd


def get_qbr_by_player_season(start_season=2023, end_season=2023, min_games=4):
    # Set season range
    season_range = [szn for szn in range(start_season, end_season + 1)]

    # Get players and QBR data
    qbr_data = nfl.import_qbr(years=season_range)
    qbr_data = qbr_data[qbr_data["season_type"] == "Regular"]
    qbr_data = qbr_data[["season", "team_abb", "player_id", "name_short", "qbr_total"]]

    # Get full ID set for players
    player_ids = nfl.import_ids()
    player_ids = player_ids[player_ids["position"] == "QB"]
    qbr_data = pd.merge(
        qbr_data, player_ids, how="inner", left_on="player_id", right_on="espn_id"
    )

    # Get basic stats for games played threshold
    season_stats = nfl.import_seasonal_data(years=season_range)
    season_stats = season_stats[season_stats["season_type"] == "REG"]
    season_stats = season_stats[["season", "player_id", "games"]]
    qbr_data = pd.merge(
        qbr_data,
        season_stats,
        how="inner",
        left_on=["season", "gsis_id"],
        right_on=["season", "player_id"],
        suffixes=(None, "_szn"),
    )

    # Get age on 09/01 of each season
    qbr_data["season_start"] = qbr_data["season"].apply(lambda szn: f"{szn}-09-01")
    qbr_data["season_start_dt"] = pd.to_datetime(qbr_data["season_start"])
    qbr_data["birthdate_dt"] = pd.to_datetime(qbr_data["birthdate"])
    qbr_data["age_season_start"] = (
        qbr_data["season_start_dt"].dt.year - qbr_data["birthdate_dt"].dt.year
    )

    # Filter for min games played
    qbr_data = qbr_data[qbr_data["games"] >= min_games]

    # Reduce columns
    qbr_data = qbr_data[
        ["season", "team_abb", "name_short", "games", "qbr_total", "age_season_start"]
    ]

    return qbr_data


def main():
    get_qbr_by_player_season()


if __name__ == "__main__":
    main()
