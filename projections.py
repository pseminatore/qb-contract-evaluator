import nfl_data_py as nfl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


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

    def project_qbr(self, n_years: int) -> dict:
        projections = {}
        base_year_adj = self._age_curve_model(self._start_age - 1)
        for yr in range(n_years):
            age = self._start_age + yr
            year_adj = self._age_curve_model(age)
            year_adj_delta = year_adj - base_year_adj
            year_proj = self._baseline_qbr_proj + year_adj_delta
            projections[age] = year_proj
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


def mean_production_before_year(row, qbr_data):
    player_qbrs = qbr_data[qbr_data["player_id"] == row["espn_id"]]
    prior_years_qbrs = player_qbrs[player_qbrs["season"] < row["year_signed"]]
    if not prior_years_qbrs.empty:
        return prior_years_qbrs["qbr_total"].mean()
    return None


def max_production_before_year(row, qbr_data):
    player_qbrs = qbr_data[qbr_data["player_id"] == row["espn_id"]]
    prior_years_qbrs = player_qbrs[player_qbrs["season"] < row["year_signed"]]
    if not prior_years_qbrs.empty:
        return prior_years_qbrs["qbr_total"].max()
    return None


def recent_production_before_year(row, qbr_data):
    player_qbrs = qbr_data[qbr_data["player_id"] == row["espn_id"]]
    prior_years_qbrs = player_qbrs[player_qbrs["season"] == row["prev_year_signed"]]
    if not prior_years_qbrs.empty:
        return prior_years_qbrs["qbr_total"][
            prior_years_qbrs["qbr_total"].first_valid_index()
        ]
    return None


def mean_wins_before_year(row, win_data):
    player_wins = win_data[win_data["winning_qb_id"] == row["gsis_id"]]
    prior_years_wins = player_wins[player_wins["season"] < row["year_signed"]]
    if not prior_years_wins.empty:
        return prior_years_wins["wins"].mean()
    return None


def max_wins_before_year(row, win_data):
    player_wins = win_data[win_data["winning_qb_id"] == row["gsis_id"]]
    prior_years_wins = player_wins[player_wins["season"] < row["year_signed"]]
    if not prior_years_wins.empty:
        return prior_years_wins["wins"].max()
    return None


def recent_wins_before_year(row, win_data):
    player_wins = win_data[win_data["winning_qb_id"] == row["gsis_id"]]
    prior_years_wins = player_wins[player_wins["season"] == row["prev_year_signed"]]
    if not prior_years_wins.empty:
        return prior_years_wins["wins"][prior_years_wins["wins"].first_valid_index()]
    return None


def build_contract_length_df(
    start_season: int = 2006, end_season: int = 2023
) -> pd.DataFrame:
    """
    features: age, avg QBR, GS, wins?, peak QBR, last season qbr, draft position
    target: years, years_guaranteed
    """

    # Set season range
    season_range = [szn for szn in range(start_season, end_season + 1)]

    # Get players and contract data
    contract_data = nfl.import_contracts()
    contract_data = contract_data[contract_data["position"] == "QB"]
    contract_data = contract_data[contract_data["year_signed"] >= start_season]
    contract_data = contract_data[contract_data["year_signed"] <= end_season]
    contract_data["prev_year_signed"] = contract_data["year_signed"] - 1
    contract_data["pct_guaranteed"] = contract_data["guaranteed"].astype(
        float
    ) / contract_data["value"].astype(float)
    contract_data["years_guaranteed"] = (
        contract_data["years"] * contract_data["pct_guaranteed"]
    )
    contract_data = contract_data[
        [
            "player",
            "gsis_id",
            "team",
            "year_signed",
            "prev_year_signed",
            "years",
            "years_guaranteed",
            "value",
            "pct_guaranteed",
            "draft_overall",
        ]
    ]
    contract_data.dropna(subset=["gsis_id"], inplace=True)

    # Get full ID set for players
    player_ids = nfl.import_ids()
    player_ids = player_ids[player_ids["position"] == "QB"]
    player_ids = player_ids[["gsis_id", "birthdate", "espn_id"]]
    contract_data = pd.merge(
        contract_data, player_ids, how="inner", left_on="gsis_id", right_on="gsis_id"
    )
    contract_data.dropna(subset=["espn_id"], inplace=True)

    # Get QBR Data
    qbr_data = nfl.import_qbr(years=season_range)
    qbr_data = qbr_data[qbr_data["season_type"] == "Regular"]
    qbr_data.dropna(subset=["player_id"], inplace=True)
    qbr_data = qbr_data[["season", "player_id", "qbr_total"]]
    contract_data["max_production_before_signing"] = contract_data.apply(
        max_production_before_year, axis=1, qbr_data=qbr_data
    )
    contract_data["mean_production_before_signing"] = contract_data.apply(
        mean_production_before_year, axis=1, qbr_data=qbr_data
    )
    contract_data["recent_production_before_signing"] = contract_data.apply(
        recent_production_before_year, axis=1, qbr_data=qbr_data
    )

    contract_data.dropna(subset=["max_production_before_signing"], inplace=True)
    contract_data.fillna(
        {
            "recent_production_before_signing": 0,
            "max_production_before_signing": 0,
            "mean_production_before_signing": 0,
        },
        inplace=True,
    )

    # Get career wins
    win_data = nfl.import_schedules(years=season_range)
    win_data = win_data[["home_qb_id", "away_qb_id", "result", "season"]]
    win_data["winning_qb_id"] = win_data["home_qb_id"].where(
        win_data["result"] > 0, win_data["away_qb_id"]
    )
    win_data = win_data[["winning_qb_id", "season", "result"]]
    win_data = win_data.groupby(by=["winning_qb_id", "season"]).count().reset_index()
    win_data.rename(columns={"result": "wins"}, inplace=True)
    contract_data["max_wins_before_signing"] = contract_data.apply(
        max_wins_before_year, axis=1, win_data=win_data
    )
    contract_data["mean_wins_before_signing"] = contract_data.apply(
        mean_wins_before_year, axis=1, win_data=win_data
    )
    contract_data["recent_wins_before_signing"] = contract_data.apply(
        recent_wins_before_year, axis=1, win_data=win_data
    )

    contract_data.dropna(subset=["max_wins_before_signing"], inplace=True)
    contract_data.fillna(
        {
            "recent_wins_before_signing": 0,
            "max_wins_before_signing": 0,
            "mean_wins_before_signing": 0,
        },
        inplace=True,
    )

    # Get age on 09/01 of each season
    contract_data["season_start"] = contract_data["year_signed"].apply(
        lambda szn: f"{szn}-09-01"
    )
    contract_data["season_start_dt"] = pd.to_datetime(contract_data["season_start"])
    contract_data["birthdate_dt"] = pd.to_datetime(contract_data["birthdate"])
    contract_data["age_season_start"] = (
        contract_data["season_start_dt"].dt.year - contract_data["birthdate_dt"].dt.year
    )
    contract_data = contract_data[
        [
            col
            for col in contract_data.columns
            if col not in ["season_start", "season_start_dt", "birthdate_dt"]
        ]
    ]

    # Fill UDFA with pick 300, slightly but noticeably later than other players
    contract_data.fillna({"draft_overall": 300}, inplace=True)

    contract_data.to_csv("contract_data_training_set.csv", index=False)

    return contract_data


def scale_data(contract_data: pd.DataFrame, features: list, targets: list) -> tuple:
    X = contract_data[features]
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_dict = {}
    for ix, colname in enumerate(features):
        X_scaled_dict[colname] = X_scaled[:, ix]
    X_scaled_df = pd.DataFrame(X_scaled_dict)
    y = contract_data[targets]
    return X_scaled_df, y, scaler


def unscale_data(
    scaled_data: pd.DataFrame, features: list, scaler: MinMaxScaler
) -> pd.DataFrame:
    scaled_data.reset_index(inplace=True)
    index = scaled_data["index"]
    scaled_data = scaled_data[features]
    scaled_data_arr = scaled_data.to_numpy()
    unscaled_data_arr = scaler.inverse_transform(scaled_data_arr)
    unscaled_data_dict = {}
    for ix, colname in enumerate(features):
        unscaled_data_dict[colname] = unscaled_data_arr[:, ix]
    unscaled_data_df = pd.DataFrame(unscaled_data_dict)
    unscaled_data_df["index"] = index
    unscaled_data_df.set_index("index", inplace=True)
    return unscaled_data_df


def predict_individual_contract(
    ct: np.ndarray, model: MultiOutputRegressor, scaler: MinMaxScaler, name: str
) -> None:
    scaled_ct = scaler.transform(ct)
    pred_ct = model.predict(scaled_ct)
    print(
        f"Projected {name} Contract: {pred_ct[0][0]:.01f} years, {pred_ct[0][1]:.02f} gtd"
    )
    return


def format_test_df(
    contract_data: pd.DataFrame,
    X_test: pd.DataFrame,
    y_pred: pd.DataFrame,
    y_act: pd.DataFrame,
) -> pd.DataFrame:
    X_test["row_num"] = range(len(X_test))
    test_output = pd.merge(X_test, y_pred, left_on="row_num", right_index=True)
    test_output = pd.merge(
        contract_data[["player", "year_signed"]],
        test_output,
        how="inner",
        left_index=True,
        right_index=True,
    )
    test_output = test_output[[col for col in test_output.columns if col != "row_num"]]
    y_act.columns = ["act_years", "act_years_guaranteed"]
    test_output = pd.merge(
        test_output, y_act, how="inner", left_index=True, right_index=True
    )
    test_output["pct_guaranteed"] = (
        test_output["years_guaranteed"] / test_output["years"]
    )
    test_output["act_pct_guaranteed"] = (
        test_output["act_years_guaranteed"] / test_output["act_years"]
    )

    test_output["years_diff"] = test_output["years"] - test_output["act_years"]
    test_output["years_diff_abs"] = test_output["years_diff"].abs()
    return test_output


def score_model(
    model: MultiOutputRegressor, X_test: pd.DataFrame, y_test: pd.DataFrame
) -> float:
    score = model.score(X_test, y_test)
    print(f"r2: {score:.02f}")
    return score


def predict_df(
    X: pd.DataFrame, targets: list, model: MultiOutputRegressor
) -> pd.DataFrame:
    y_pred = model.predict(X)
    y_pred_dict = {}
    for ix, colname in enumerate(targets):
        y_pred_dict[colname] = y_pred[:, ix]
    unscaled_data_df = pd.DataFrame(y_pred_dict)
    return unscaled_data_df


def build_model(contract_data: pd.DataFrame):
    targets = ["years", "years_guaranteed"]
    features = [
        "age_season_start",
        "draft_overall",
        "max_production_before_signing",
        "mean_production_before_signing",
        "recent_production_before_signing",
        "max_wins_before_signing",
        "mean_wins_before_signing",
        "recent_wins_before_signing",
    ]

    X, y, scaler = scale_data(contract_data, features, targets)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    model = MultiOutputRegressor(
        KNeighborsRegressor(n_neighbors=3, weights="distance")
    ).fit(X_train, y_train)

    score = score_model(model, X_test, y_test)

    y_pred = predict_df(X_test, targets, model)

    # predict_individual_contract(
    #     np.array([[27, 64, 60.5, 53.0, 60.5]]), model, scaler, "Darnold"
    # )
    predict_individual_contract(
        np.array([[21, 1.0, 74.7, 64.0, 74.7, 14.0, 10, 14.0]]), model, scaler, "Burrow"
    )

    X_test_unscaled = unscale_data(X_test.copy(), features, scaler)
    test_df = format_test_df(contract_data, X_test_unscaled, y_pred, y_test)

    return model


def main():

    # contract_data = build_contract_length_df()
    contract_data = pd.read_csv("contract_data_training_set.csv")
    model = build_model(contract_data)

    start_age = 32
    baseline_qbr_proj = 60.7
    years = 3
    aging_curve = BasicAgingCurve(start_age, baseline_qbr_proj)
    qbr_projections = aging_curve.project_qbr(n_years=years)
    print(qbr_projections)


if __name__ == "__main__":
    main()
