import nfl_data_py as nfl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json


class BasicAgingCurveBuilder:

    def __init__(
        self,
        retirement_decay: int = 1,
        curve_degree: int = 4,
        show_plot: bool = False,
        dump_coeffs: bool = True,
        coeff_filepath: str = "age_curve_coeff.json",
        start_season: int = 2006,
        end_season: int = 2023,
        min_games: int = 4,
    ) -> None:
        self._retirement_decay = retirement_decay
        self._curve_degree = curve_degree
        self._show_plot = show_plot
        self._dump_coeffs = dump_coeffs
        self._coeff_filepath = coeff_filepath
        self._start_season = start_season
        self._end_season = end_season
        self._min_games = min_games
        return

    def build(self) -> np.poly1d:
        qbr_seasons = self.get_qbr_by_player_season(
            self._start_season, self._end_season, self._min_games
        )
        avg_delta_by_age = self.get_avg_delta_by_age(
            qbr_seasons, self._retirement_decay
        )
        age_curve_model = self.fit_qbr_curve(
            avg_delta_by_age,
            show_plot=self._show_plot,
            dump_coeffs=self._dump_coeffs,
            curve_degree=self._curve_degree,
        )
        return age_curve_model

    def get_qbr_by_player_season(self, start_season=2006, end_season=2023, min_games=4):
        # Set season range
        season_range = [szn for szn in range(start_season, end_season + 1)]

        # Get players and QBR data
        qbr_data = nfl.import_qbr(years=season_range)
        qbr_data = qbr_data[qbr_data["season_type"] == "Regular"]
        qbr_data = qbr_data[
            ["season", "team_abb", "player_id", "name_short", "qbr_total"]
        ]

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

        ## TODO - Get QBR above AVG

        # Reduce columns
        qbr_data = qbr_data[
            [
                "season",
                "team_abb",
                "name_short",
                "games",
                "qbr_total",
                "age_season_start",
            ]
        ]

        return qbr_data

    def get_avg_delta_by_age(self, qbr_seasons: pd.DataFrame, retirement_decay=1):
        qbr_seasons.sort_values(
            by=["name_short", "season"], inplace=True, ignore_index=True
        )

        # Pad seasons after retirement with 0 QBR to influence downswing
        for offset in range(1, retirement_decay + 1):
            new_rows = []
            for player in qbr_seasons["name_short"].unique():
                last_index = qbr_seasons[qbr_seasons["name_short"] == player].index[-1]
                new_row = {
                    "season": qbr_seasons.iat[last_index, 0] + offset,
                    "team_abb": qbr_seasons.iat[last_index, 1],
                    "name_short": player,
                    "games": 0,
                    "qbr_total": 0.0,
                    "age_season_start": qbr_seasons.iat[last_index, 5] + offset,
                }
                new_rows.append(new_row)
            qbr_seasons = pd.concat(
                [qbr_seasons, pd.DataFrame(new_rows)], ignore_index=True
            )
        qbr_seasons.sort_values(
            by=["name_short", "season"], inplace=True, ignore_index=True
        )

        # Account for playing time
        qbr_seasons["season_max_games"] = np.where(qbr_seasons["season"] < 2021, 16, 17)
        qbr_seasons["qbr_weighted"] = (
            qbr_seasons["qbr_total"] / qbr_seasons["season_max_games"]
        ) * qbr_seasons["games"]

        # Get delta of weighted avg across seasons
        qbr_seasons["qbr_prev"] = qbr_seasons.groupby(by="name_short")[
            "qbr_weighted"
        ].shift(1)
        qbr_seasons["qbr_delta"] = qbr_seasons["qbr_total"] - qbr_seasons["qbr_prev"]

        # Group deltas by age bucket
        qbr_seasons_by_age = (
            qbr_seasons[["age_season_start", "qbr_delta"]]
            .groupby(by="age_season_start")
            .agg({"qbr_delta": ["mean", "count"]})
            .reset_index()
        )
        qbr_seasons_by_age.columns = [
            "_".join(col).strip() for col in qbr_seasons_by_age.columns.values
        ]
        qbr_seasons_by_age["chained_qbr_delta"] = qbr_seasons_by_age[
            "qbr_delta_mean"
        ].cumsum()

        # Center deltas around 0
        qbr_seasons_by_age["chained_qbr_delta"] = (
            qbr_seasons_by_age["chained_qbr_delta"]
            - qbr_seasons_by_age["chained_qbr_delta"][
                qbr_seasons_by_age["chained_qbr_delta"].first_valid_index()
            ]
        )
        return qbr_seasons_by_age

    def fit_qbr_curve(
        self,
        age_delta: pd.DataFrame,
        curve_degree=4,
        show_plot=True,
        dump_coeffs=False,
        coeff_filepath="age_curve_coeff.json",
    ) -> np.poly1d:
        x = age_delta["age_season_start_"].to_numpy()[1:]
        y = age_delta["chained_qbr_delta"].to_numpy()[1:]

        # Fit a 2nd-degree polynomial to the data
        coefficients = np.polyfit(x, y, curve_degree)

        # Optionally output coefficients to file
        if dump_coeffs:
            self.save_model_coefficients(coefficients, coeff_filepath)

        # Create a function for the fitted curve
        p = np.poly1d(coefficients)

        # Evaluate the fitted curve at the given x-values
        y_fit = p(x)

        if show_plot:
            fig = px.scatter(age_delta, x="age_season_start_", y="chained_qbr_delta")
            fig.add_trace(go.Scatter(x=x, y=y_fit, mode="lines", name="model"))
            fig.show()

        return p

    def save_model_coefficients(
        self, coeffs: np.ndarray, filepath="age_curve_coeff.json"
    ):
        coeff_arr = coeffs.tolist()
        coeff_obj = {"coeffs": coeff_arr}
        with open(filepath, "w") as f:
            json.dump(coeff_obj, f)
        return


class BasicAgingCurve:

    def __init__(
        self,
        start_age: int,
        baseline_qbr_proj: float,
        coeff_filepath: str = "age_curve_coeff.json",
    ) -> None:
        self._start_age = start_age
        self._baseline_qbr_proj = baseline_qbr_proj
        self._coeff_filepath = coeff_filepath
        self._age_curve_model = self.load_model(self._coeff_filepath)
        return

    def project_qbr(self, n_years: int) -> list:
        projections = []
        base_year_adj = self._age_curve_model(self._start_age - 1)
        for yr in range(n_years):
            age = self._start_age + yr
            year_adj = self._age_curve_model(age)
            year_adj_delta = year_adj - base_year_adj
            year_proj = self._baseline_qbr_proj + year_adj_delta
            projections.append(year_proj)
        return projections

    def load_model_coefficients(self, filepath="age_curve_coeff.json") -> np.array:
        with open(filepath, "r") as f:
            coeff_obj = json.load(f)
        coeff_arr = coeff_obj.get("coeffs", [])
        coeffs = np.array(coeff_arr)
        return coeffs

    def load_model(self, filepath="age_curve_coeff.json") -> np.poly1d:
        coefficients = self.load_model_coefficients(filepath=filepath)
        model_func = np.poly1d(coefficients)
        return model_func


def main():

    start_age = 28
    baseline_qbr_proj = 60.7
    years = 3
    aging_curve = BasicAgingCurve(start_age, baseline_qbr_proj)
    qbr_projections = aging_curve.project_qbr(n_years=years)
    print(qbr_projections)


if __name__ == "__main__":
    main()
