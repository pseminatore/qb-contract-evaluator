import pandas as pd
from value import market_value as eval_market_value
import tabulate
import plotly.graph_objects as go
import plotly.colors as colors
import os


class Contract:
    seasons: list = []

    has_option_years: bool = False
    has_void_years: bool = False

    total_value: float = None

    breakdown: list = None

    def __init__(
        self,
        start_year: int = None,
        end_year: int = None,
        salaries: list = [],
        option_year: int = None,
        option_salaries: list = [],
        option_dead_caps: list = [],
        void_year: int = None,
        void_year_dead_caps: list = [],
    ) -> None:
        if start_year is None or end_year is None:
            return
        option_ix = 0
        void_ix = 0
        for ix, season in enumerate(range(start_year, end_year)):
            salary = salaries[ix]
            is_option_year = season >= option_year
            is_void_year = season >= void_year
            if is_option_year:
                option_salary = option_salaries[option_ix]
                option_dead_cap = option_dead_caps[option_ix]
                option_ix += 1
                self.has_option_years = True
            else:
                option_salary = None
                option_dead_cap = None

            if is_void_year:
                void_dead_cap = void_year_dead_caps[void_ix]
                void_ix += 1
                self.has_void_years = True
            else:
                void_dead_cap = None

            contract_season = ContractSeason(
                season,
                is_option_year,
                is_void_year,
                salary,
                option_salary,
                option_dead_cap,
                void_dead_cap,
            )
            self.seasons.append(contract_season)
        self.sort()
        self.set_total_value()

    def __iter__(self):
        return (
            (contract_season.year, contract_season) for contract_season in self.seasons
        )

    def __str__(self):
        if not self.breakdown:
            self.generate_breakdown()
        headers = self.breakdown[0].keys()
        rows = [x.values() for x in self.breakdown]
        return tabulate.tabulate(rows, headers)

    def __repr__(self) -> str:
        start_year = self.seasons[0].year
        end_year = self.seasons[-1].year
        if self.total_value:
            return f"Contract({start_year}-{end_year}: ${self.total_value:.1f}M)"
        return f"Contract({start_year}-{end_year})"

    def __getitem__(self, ix):
        return self.seasons[ix]

    def sort(self) -> None:
        self.seasons.sort(key=lambda x: x.year)
        return

    def from_records(self, season_records) -> None:
        for season in season_records:
            season_obj = ContractSeason().from_dict(season)

            if season_obj.is_option_year:
                self.has_option_years = True
            if season_obj.is_void_year:
                self.has_void_years = True

            self.seasons.append(season_obj)
        self.sort()
        self.set_total_value()
        return self

    def to_records(self) -> list:
        rc = []
        for season in self.seasons:
            rc.append(season.to_dict())
        return rc

    def to_df(self) -> pd.DataFrame:
        df = pd.DataFrame().from_records(self.to_records())
        return df

    def generate_breakdown(self):
        breakdown = []
        for contract_season in self.seasons:
            # Format breakdown row
            season_breakdown = {
                "Season": contract_season.year,
                "Base Sal": contract_season.salary,
            }
            if self.has_option_years:
                season_breakdown["Option Sal"] = (
                    contract_season.option_salary
                    if contract_season.is_option_year
                    else "--"
                )
            if self.has_void_years:
                season_breakdown["Void Sal"] = (
                    contract_season.void_dead_cap
                    if contract_season.is_void_year
                    else "--"
                )

            # Append breakdown row
            breakdown.append(season_breakdown)

        # Set as property
        self.breakdown = breakdown

    def set_total_value(self):
        total_value = 0.0
        for contract_season in self.seasons:
            if contract_season.is_void_year:
                total_value += contract_season.void_dead_cap
            elif contract_season.is_option_year:
                total_value += contract_season.option_salary
            else:
                total_value += contract_season.salary
        self.total_value = total_value
        return


class ContractSeason:
    year: int
    is_option_year: bool
    is_option_tendered: bool
    is_void_year: bool
    salary: float
    option_salary: float
    option_dead_cap: float
    void_dead_cap: float

    production: int
    inflation_adj: float
    market_salary: float
    actual_salary: float
    surplus_value: float = 0.0

    def __init__(
        self,
        year=None,
        is_option_year=None,
        is_void_year=None,
        salary=None,
        option_salary=None,
        option_dead_cap=None,
        void_dead_cap=None,
        production=None,
        inflation_adj=None,
        market_salary=None,
        actual_salary=None,
        surplus_value=0.0,
    ) -> None:
        self.year = year
        self.is_option_year = is_option_year
        self.is_void_year = is_void_year
        self.salary = salary
        self.option_salary = option_salary
        self.option_dead_cap = option_dead_cap
        self.void_dead_cap = void_dead_cap
        self.production = production
        self.inflation_adj = inflation_adj
        self.market_salary = market_salary
        self.actual_salary = actual_salary
        self.surplus_value = surplus_value

    def __str__(self):
        as_dict = self.to_dict()
        headers = as_dict.keys()
        rows = [as_dict.values()]
        return tabulate.tabulate(rows, headers)

    def __repr__(self) -> str:
        if self.production is not None:
            return f"ContractSeason({self.year}: ${self.salary:.1f}M - {self.production} QBR)"
        return f"ContractSeason({self.year}: ${self.salary:.1f}M)"

    def from_dict(self, dict) -> None:
        self.__init__(**dict)
        return self

    def to_dict(self) -> dict:
        dt = {}
        # Standard properties
        dt["year"] = self.year
        dt["is_option_year"] = self.is_option_year
        dt["is_void_year"] = self.is_void_year
        dt["salary"] = self.salary
        dt["option_salary"] = self.option_salary
        dt["option_dead_cap"] = self.option_dead_cap
        dt["void_dead_cap"] = self.void_dead_cap

        # Optional properties
        if self.production is not None:
            dt["prod"] = self.production
        if self.inflation_adj is not None:
            dt["inflation_adj"] = self.inflation_adj
        if self.market_salary is not None:
            dt["market_salary"] = self.market_salary
        if self.actual_salary is not None:
            dt["actual_salary"] = self.actual_salary
        if self.surplus_value is not None:
            dt["surplus_value"] = self.surplus_value
        return dt


class ContractEvaluation(Contract):
    productions: list = []

    is_option_declined: bool = False

    option_years_tendered_value: float
    option_years_declined_value: float

    surplus_value: float = None
    market_value: float = None
    player_name: str = None

    def __init__(
        self, contract: Contract = None, productions: list = [], player_name: str = None
    ) -> None:
        self.productions = productions
        self.has_option_years = contract.has_option_years
        self.has_void_years = contract.has_void_years
        self.player_name = player_name
        for ix, ((_, contract_season), production) in enumerate(
            zip(contract, productions)
        ):
            contract_season.production = production
            self.seasons[ix] = contract_season
        return

    def __repr__(self) -> str:
        start_year = self.seasons[0].year
        end_year = self.seasons[-1].year
        if self.surplus_value is not None:
            return f"ContractEvaluation({start_year}-{end_year}: ${self.surplus_value:.1f}M)"
        return f"ContractEvaluation({start_year}-{end_year})"

    def set_productions(self, productions: list):
        for contract_season, prod in zip(self.seasons, productions):
            contract_season.production = prod
        return

    def get_remaining_val(self, start_year: int):
        remaining_val = 0.0
        for year, contract_season in self.__iter__():
            if year < start_year:
                continue
            if contract_season.is_void_year:
                remaining_val -= contract_season.void_dead_cap
            else:
                market_val, _ = eval_market_value(contract_season.production, year)
                remaining_val += market_val - contract_season.option_salary
        return remaining_val

    def decline_option_years(self, start_year: int):
        self.is_option_declined = True
        for year, contract_season in self.__iter__():
            if year < start_year:
                continue
            contract_season.is_option_tendered = False
            contract_season.actual_salary = (
                contract_season.void_dead_cap
                if contract_season.is_void_year
                else contract_season.option_dead_cap
            )
            contract_season.production = 0
            contract_season.market_salary = 0.0
        return

    def generate_breakdown(self):
        if not self.market_value:
            self.evaluate()
        breakdown = []
        for contract_season in self.seasons:
            # Format breakdown row
            season_breakdown = {
                "Season": contract_season.year,
                "QBR": contract_season.production,
                "Market Sal": contract_season.market_salary,
                "Actual Sal": contract_season.actual_salary,
                "Inflation Adj": contract_season.inflation_adj,
                "Tot. Surplus Value": contract_season.surplus_value,
            }
            if self.has_option_years:
                season_breakdown["Option Sal"] = (
                    contract_season.option_salary
                    if contract_season.is_option_year
                    else "--"
                )
            if self.has_void_years:
                season_breakdown["Void Sal"] = (
                    contract_season.void_dead_cap
                    if contract_season.is_void_year
                    else "--"
                )

            # Append breakdown row
            breakdown.append(season_breakdown)

        # Set as property
        self.breakdown = breakdown

    def evaluate(self):
        # Reset value sums in case productions have changed
        self.reset_values()

        for year, contract_season in self.__iter__():
            # Get contract values
            val_prod, inflation_adj = eval_market_value(
                contract_season.production, year
            )

            # Set base values in season
            contract_season.inflation_adj = inflation_adj
            contract_season.market_salary = (
                contract_season.market_salary
                if contract_season.is_option_year and self.is_option_declined
                else val_prod
            )
            contract_season.actual_salary = contract_season.salary

            # Option handling - skip if option has already been declined
            if contract_season.is_option_year and not self.is_option_declined:
                # Get the value of the option
                remaining_surplus_val = self.get_remaining_val(year)

                # Option will be declined if it has negative value, else it will be tendered
                if remaining_surplus_val < 0:
                    self.decline_option_years(year)
                else:
                    # tender the option
                    contract_season.actual_salary = contract_season.option_salary
                    contract_season.is_option_tendered = True

            # Void year handling
            if contract_season.is_void_year:
                contract_season.market_salary = 0.0
                contract_season.actual_salary = contract_season.void_dead_cap

            # Get surplus value of season
            contract_season.surplus_value = (
                contract_season.market_salary - contract_season.actual_salary
            )

            # Accumulate contract value
            self.surplus_value += contract_season.surplus_value
            self.market_value += contract_season.market_salary
            self.total_value += contract_season.actual_salary

        # Generate Breakdown
        self.generate_breakdown()

        return self.surplus_value

    def reset_values(self):
        self.market_value = 0.0
        self.surplus_value = 0.0
        self.total_value = 0.0

    def build_surplus_value_graphic(self, save_show=False):
        if not self.breakdown:
            self.generate_breakdown()
        fig = go.Figure()
        leaderboard = self.to_df()
        leaderboard.rename(
            columns={
                "year": "Season",
                "prod": "Proj. QBR",
                "market_salary": "Market Sal. ($M)",
                "actual_salary": "Actual Sal. ($M)",
                "inflation_adj": "Inflation Adj",
                "surplus_value": "Surplus Val ($M)",
            },
            inplace=True,
        )
        header_cols = [
            "Season",
            "Proj. QBR",
            "Market Sal. ($M)",
            "Actual Sal. ($M)",
            "Inflation Adj",
            "Surplus Val ($M)",
        ]
        normalized_colorpoints = (leaderboard["Surplus Val ($M)"] + 70) / 140
        colors_arr = colors.sample_colorscale(
            "RdBu_r", normalized_colorpoints, low=0, high=1.0
        )
        leaderboard["border_color"] = [
            (
                "rgb(217, 173, 28)"
                if (self.has_void_years) and szn.is_void_year
                else (
                    "rgb(40, 161, 66)"
                    if self.has_option_years
                    and szn.is_option_year
                    and szn.is_option_tendered
                    else (
                        "rgb(201, 43, 28)"
                        if self.has_option_years
                        and szn.is_option_year
                        and not szn.is_option_tendered
                        else "grey"
                    )
                )
            )
            for _, szn in self.__iter__()
        ]
        leaderboard["border_size"] = [
            (5 if szn.is_option_year or szn.is_void_year else 1)
            for _, szn in self.__iter__()
        ]
        fill_colors = ["rgb(237,237,237)" for _ in range(len(header_cols) - 1)] + [
            colors_arr
        ]
        line_widths = []
        for _ in header_cols:
            for _, season in self.__iter__():
                width = (
                    5
                    if (self.has_option_years and season.is_option_year)
                    or (self.has_void_years and season.is_void_year)
                    else 1
                )
                line_widths.append(width)

        title = f"Surplus Value Breakdown"
        surplus_value_str = f"Contract Surplus Value: "
        surplus_value_amount = f"${self.surplus_value:.01f}"
        surplus_value_str_color = (
            "rgb(50, 168, 60)" if self.surplus_value > 0 else "rgb(168, 50, 60)"
        )
        fig.add_annotation(
            xref="x domain",
            yref="paper",
            x=0.5,
            y=1.025,
            showarrow=False,
            text=title,
            font=dict(size=42),
        )
        fig.add_annotation(
            xref="x domain",
            yref="paper",
            x=0.5,
            y=0.9975,
            showarrow=False,
            text=self.player_name,
            font=dict(size=38),
        )
        fig.add_annotation(
            xref="x domain",
            yref="paper",
            x=0.4,
            y=0.975,
            showarrow=False,
            text=surplus_value_str,
            font=dict(size=38),
        )
        fig.add_annotation(
            xref="x domain",
            yref="paper",
            x=0.785,
            y=0.975,
            showarrow=False,
            text=surplus_value_amount,
            font=dict(size=38, color=surplus_value_str_color),
        )
        fig.add_annotation(
            xref="x domain",
            yref="y domain",
            x=0.05,
            y=0.58,
            showarrow=False,
            text="Green: Tendered Option Year",
            font=dict(size=24, color="rgb(40, 161, 66)"),
        )
        fig.add_annotation(
            xref="x domain",
            yref="y domain",
            x=0.05,
            y=0.56,
            showarrow=False,
            text="Red: Declined Option Year",
            font=dict(size=24, color="rgb(201, 43, 28)"),
        )
        fig.add_annotation(
            xref="x domain",
            yref="y domain",
            x=0.05,
            y=0.54,
            showarrow=False,
            text="Yellow: Void Year",
            font=dict(size=24, color="rgb(217, 173, 28)"),
        )
        fig.add_trace(
            go.Table(
                header=dict(
                    values=header_cols,
                    height=56,
                    font=dict(size=35),
                    line_width=3,
                    line_color="grey",
                ),
                cells=dict(
                    values=[
                        leaderboard["Season"],
                        leaderboard["Proj. QBR"],
                        round(leaderboard["Market Sal. ($M)"], 1),
                        round(leaderboard["Actual Sal. ($M)"], 1),
                        round(leaderboard["Inflation Adj"], 3),
                        round(leaderboard["Surplus Val ($M)"], 1),
                    ],
                    height=55,
                    font=dict(size=38),
                    fill_color=fill_colors,
                    line_color=[leaderboard["border_color"]],
                    line_width=5,
                    prefix=["", "", "$", "$", "", "$"],
                ),
                domain=dict(y=[0, 0.92]),
            )
        )
        fig.update_layout(
            width=1080,
            height=2000,
            template="ggplot2",
        )
        if save_show:
            fig.show()
        else:
            if not os.path.exists(f"outputs/contract_breakdowns"):
                os.mkdir(f"outputs/contract_breakdowns")
            fig.write_image(f"outputs/contract_breakdowns/{self.player_name}.png")
        return
