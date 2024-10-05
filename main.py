from value import generic_qb_av_table
from graphics import build_surplus_value_graphic
from utils import *


    
    
def evaluate_contract(seasons, salary_func, prod_func, option_func=None, void_func=None):
    production = prod_func()
    options = option_func() if option_func is not None else None
    voids = void_func() if void_func is not None else None
    sum_value, av_breakdown = generic_qb_av_table(seasons, production, salary_func, options, voids)
    print_breakdown(av_breakdown)
    build_surplus_value_graphic(av_breakdown, sum_value, 'Dak Prescott', save_show=False, option_year=2028)


if __name__ == '__main__':
    seasons = [i for i in range(2024, 2033)]
    evaluate_contract(seasons, salary_prescott_actual, production_curve_prescott, option_func=prescott_option_years)
    
