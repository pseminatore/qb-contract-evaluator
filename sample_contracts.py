from contract import Contract, ContractEvaluation
from utils import production_curve_lawrence
from compare import find_breakeven_point


def prescott_contract():
    ct = Contract(
        start_year=2024,
        end_year=2028,
        salaries=[43.4, 89.9, 68.0, 62.0, 0.0],
        option_year=2028,
        option_salaries=[72.0],
        option_dead_caps=34.0,
    )


def lawrence_contract():
    dt = [
        {
            "year": 2024,
            "is_option_year": False,
            "is_void_year": False,
            "salary": 15.0,
        },
        {
            "year": 2025,
            "is_option_year": False,
            "is_void_year": False,
            "salary": 17.0,
        },
        {
            "year": 2026,
            "is_option_year": False,
            "is_void_year": False,
            "salary": 24.0,
        },
        {
            "year": 2027,
            "is_option_year": False,
            "is_void_year": False,
            "salary": 35.0,
        },
        {
            "year": 2028,
            "is_option_year": False,
            "is_void_year": False,
            "salary": 47.0,
        },
        {
            "year": 2029,
            "is_option_year": True,
            "is_void_year": False,
            "salary": 0.0,
            "option_salary": 78.5,
            "option_dead_cap": 0.0,
        },
        {
            "year": 2030,
            "is_option_year": True,
            "is_void_year": False,
            "salary": 0.0,
            "option_salary": 74.8,
            "option_dead_cap": 0.0,
        },
        {
            "year": 2031,
            "is_option_year": False,
            "is_void_year": True,
            "salary": 0.0,
            "void_dead_cap": 21.0,
        },
    ]
    ct = Contract().from_records(dt)
    return ct


if __name__ == "__main__":
    ct = lawrence_contract()
    val = find_breakeven_point(ct)
    # print(ct)
    prods = production_curve_lawrence()
    eval_ct = ContractEvaluation(ct, prods, "Trevor Lawrence")
    print(eval_ct)
    eval_ct.build_surplus_value_graphic()
    print(ct)

    season = eval_ct[0]
    print(season)
