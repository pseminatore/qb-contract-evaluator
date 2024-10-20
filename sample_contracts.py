from contract import Contract
from utils import production_curve_lawrence


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
    prods = production_curve_lawrence()
    ct.evaluate(prods)
    season = ct[0]
    print(season)
