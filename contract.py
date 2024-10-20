import pandas as pd
from value import market_value as eval_market_value
import tabulate


class Contract:
    seasons: list = []

    has_option_years: bool
    has_void_years: bool

    is_option_declined: bool = False

    option_years_tendered_value: float
    option_years_declined_value: float

    surplus_value: float = 0.0
    total_value: float = 0.0
    market_value: float = 0.0

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
            base_salary = salaries[ix]
            is_option_year = season >= option_year
            is_void_year = season >= void_year
            if is_option_year:
                option_salary = option_salaries[option_ix]
                option_dead_cap = option_dead_caps[option_ix]
                option_ix += 1
            else:
                option_salary = None
                option_dead_cap = None

            if is_void_year:
                void_dead_cap = void_year_dead_caps[void_ix]
                void_ix += 1
            else:
                void_dead_cap = None

            contract_season = ContractSeason(
                season,
                is_option_year,
                is_void_year,
                base_salary,
                option_salary,
                option_dead_cap,
                void_dead_cap,
            )
            self.seasons.append(contract_season)
        self.sort()

    def __iter__(self):
        return (
            (contract_season.year, contract_season) for contract_season in self.seasons
        )

    def __str__(self):
        if not len(self.breakdown) > 0:
            return
        headers = self.breakdown[0].keys()
        rows = [x.values() for x in self.breakdown]
        return tabulate.tabulate(rows, headers)

    def option_years(self) -> list:
        return self.options.keys()

    def option_dead_cap(self) -> list:
        return self.options.values()

    def void_years(self) -> list:
        return self.voids.keys()

    def void_dead_cap(self) -> list:
        return self.voids.values()

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
        return self

    def to_records(self) -> list:
        rc = []
        for season in self.seasons:
            rc.append(season.to_dict())
        return rc

    def to_df(self) -> pd.DataFrame:
        df = pd.DataFrame().from_records(self.to_records())
        return df

    def set_productions(self, productions: list):
        for contract_season, prod in zip(self.seasons, productions):
            contract_season.production = prod
        return

    def evaluate(self, productions: list):
        self.set_productions(productions)
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
            contract_season.actual_salary = contract_season.base_salary

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

            if year == 2030:
                print(contract_season.market_salary)

        # Generate Breakdown
        self.generate_breakdown()

        return self.surplus_value

    def generate_breakdown(self):
        breakdown = []
        for contract_season in self.seasons:
            # Format breakdown row
            season_breakdown = {
                "Season": contract_season.year,
                "QBR": contract_season.production,
                "Market Sal": contract_season.market_salary,
                "Actual Sal": contract_season.base_salary,
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


class ContractSeason:
    year: int
    is_option_year: bool
    is_option_tendered: bool
    is_void_year: bool
    base_salary: float
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
        base_salary=None,
        option_salary=None,
        option_dead_cap=None,
        void_dead_cap=None,
    ) -> None:
        self.year = year
        self.is_option_year = is_option_year
        self.is_void_year = is_void_year
        self.base_salary = base_salary
        self.option_salary = option_salary
        self.option_dead_cap = option_dead_cap
        self.void_dead_cap = void_dead_cap

    def __str__(self):
        pass

    def from_dict(self, dict) -> None:
        self.__init__(**dict)
        return self

    def to_dict(self) -> dict:
        dt = {}
        dt["year"] = self.year
        dt["is_option_year"] = self.is_option_year
        dt["is_void_year"] = self.is_void_year
        dt["base_salary"] = self.base_salary
        dt["option_salary"] = self.option_salary
        dt["option_dead_cap"] = self.option_dead_cap
        dt["void_dead_cap"] = self.void_dead_cap
        return dt
