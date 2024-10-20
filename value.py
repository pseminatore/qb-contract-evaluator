from utils import inflation_coeff, salary_cousins_actual, salary_penix_actual
import math
from scipy.optimize import minimize


def get_apy_prod_value_exp(prod):
    """Get the raw value in dollars of QBR using exponential model"""
    value = 1.631 * (math.exp(0.0461 * prod))
    return value


def get_apy_prod_value_pow(prod):
    """Get the raw value in dollars of QBR using power model"""
    value = 0.0016 * (prod**2.23796)
    return value


def get_apy_prod_value_3_poly(prod):
    """Get the raw value in dollars of QBR using 3rd order polynomial model"""
    x3 = -0.000231 * (prod**3)
    x2 = 0.0412 * (prod**2)
    x = -0.997 * prod
    b = 6.75
    value = x3 + x2 + x + b
    return value


def get_apy_prod_value_2_poly(prod):
    """Get the raw value in dollars of QBR using 2nd order polynomial model"""
    x2 = 0.009 * (prod**2)
    x = 0.0393 * prod
    b = -6.2733
    value = x2 + x + b
    return value


def get_apy_prod_value_6_poly(prod):
    """Get the raw value in dollars of QBR using 2nd order polynomial model"""
    x6 = 0.00000000662 * (prod**6)
    x5 = -0.00000186 * (prod**5)
    x4 = 0.0001884 * (prod**4)
    x3 = -0.00839 * (prod**3)
    x2 = 0.1695 * (prod**2)
    x = -1.15 * (prod**1)
    b = 5.05
    value = x6 + x5 + x4 + x3 + x2 + x + b
    return value


def market_value(prod, season, prod_function=get_apy_prod_value_6_poly):
    """Get value of production in a given season"""
    season_offset = season - 2024
    # Lower bound for starting QB is ~40 QBR.  Anything lower is worse than replacement
    raw_prod_value = prod_function(prod)  # if prod >= 40.0 else 8
    inflation_adj = inflation_coeff(season_offset)
    production_value = raw_prod_value * inflation_adj
    return production_value, inflation_adj


def generic_qb_av_table(
    seasons, productions, salary_func, option_years=None, void_years=None
):
    surplus_val = 0
    breakdown = []
    has_option = option_years is not None
    has_void = void_years is not None
    for season, prod in zip(seasons, productions):
        val_prod, inflation_adj = market_value(prod, season)
        val_act = salary_func(season)
        # if val_act == 0.0 :
        #     prod = 0
        #     val_prod = 0

        if option_years is not None and season in option_years.keys():
            val_act = option_years[season]

        if void_years is not None and season in void_years.keys():
            val_prod = 0.0
            val_act = void_years[season]

        season_val = val_prod - val_act
        total_surplus_value = season_val
        season_breakdown = {
            "Season": season,
            "QBR": prod,
            "Market Sal": val_prod,
            "Actual Sal": val_act,
            "Inflation Adj": inflation_adj,
            "Tot. Surplus Value": total_surplus_value,
        }
        if has_option:
            season_breakdown["Option Sal"] = option_years.get(season, "--")
        if has_void:
            season_breakdown["Void Sal"] = void_years.get(season, "--")
        breakdown.append(season_breakdown)
        surplus_val += total_surplus_value

    return surplus_val, breakdown


# def generic_qb_av_table_from_contract(productions, contract: Contract):
#     breakdown = []
#     for (year, contract_season), prod in zip(contract, productions):
#         # Get contract values
#         val_prod, inflation_adj = market_value(prod, year)
#         val_act = get_apy_prod_value_6_poly(year)

#         # Set in season
#         contract_season.market_value = val_prod
#         contract_season.surplus_value = total_surplus_value


#         # Option handling
#         if contract_season.is_option_year:
#             val_act = contract_season.option_salary

#         # Void year handling
#         if contract_season.is_void_year:
#             val_prod = 0.0
#             val_act = contract_season.void_dead_cap

#         season_val = val_prod - val_act
#         total_surplus_value = season_val


#         season_breakdown = {'Season': year, 'QBR': prod, 'Market Sal': val_prod, 'Actual Sal': val_act, 'Inflation Adj': inflation_adj,'Tot. Surplus Value': total_surplus_value}
#         if contract.has_option_years:
#             season_breakdown['Option Sal'] = contract_season.option_salary if contract_season.is_option_year else '--'
#         if contract.has_void_years:
#             season_breakdown['Void Sal'] = contract_season.void_dead_cap if contract_season.is_void_year else '--'
#         breakdown.append(season_breakdown)
#         surplus_val += total_surplus_value

#     return surplus_val, breakdown


# def handle_options(contract: Contract):
#     # If no option years, do nothing
#     if not contract.has_option_years:
#         return contract

#     # If there are options, consider the value of each option year
#     for year, contract_season in contract:

#         # Seek to option year
#         if not contract_season.is_option_year:
#             continue


def defender_const_production():
    production_value = 20
    actual_salary = 6.75
    surplus_value = production_value - actual_salary
    return surplus_value


# def find_breakeven_point(cousins_prod, verbose=False):
#     # X axis value
#     v_no_penix, _ = find_no_penix_av(cousins_prod)

#     # Find the equivalent Penix production level
#     min_result = minimize(find_penix_equal_prod, [50], args=(v_no_penix, cousins_prod, verbose), bounds=[(40, None)])

#     penix_equal_prod = min_result.x[0]

#     return penix_equal_prod
