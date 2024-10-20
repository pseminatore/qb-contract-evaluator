import tabulate


def salary_cousins_actual(season):
    cap_salaries = {
        2024: 25.0,
        2025: 40.0,
        2026: 57.5,
        2027: 57.5,
    }
    return cap_salaries.get(season, 0.0)


def salary_penix_actual(season):
    cap_salaries = {2024: 12, 2025: 12, 2026: 12, 2027: 12, 2028: 12}
    return cap_salaries.get(season, 0.0)


def cost_per_win_qb(season):
    season = season - 2000
    cpw = (0.0710714 * season) - 0.7805
    return cpw


def print_tabular_pts(xs, ys):
    for x, y in zip(xs, ys):
        print(f"{x}\t{y}")


def print_breakdown(breakdown):
    if not len(breakdown) > 0:
        return
    headers = breakdown[0].keys()
    rows = [x.values() for x in breakdown]
    print(tabulate.tabulate(rows, headers))


def inflation_coeff(season_offset):
    """Account for salary cap inflation each year after deal is signed"""
    inflation_rate = 1.0858
    return inflation_rate**season_offset


def salary_prescott_actual(season):
    cap_salaries = {
        2024: 43.4,
        2025: 89.9,
        2026: 68.0,
        2027: 62.0,
        2028: 34.0,
    }
    return cap_salaries.get(season, 0.0)


def production_curve_prescott():
    prods = [
        70,
        71,
        72,
        70,
        65,
    ]
    return prods


def prescott_option_years():
    """Returns dict of format {year: dead cap if declined}"""
    options = {2028: 72.0}
    return options


def salary_lawrence_actual(season):
    cap_salaries = {
        2024: 15.0,
        2025: 17.0,
        2026: 24.0,
        2027: 35.0,
        2028: 47.0,
        2029: 0.0,
        2030: 0.0,
        2031: 0.0,
    }
    return cap_salaries.get(season, 0.0)


def production_curve_lawrence():
    prods = [
        56,
        57,
        59,
        59,
        57,
        57,
        56,
        0,
    ]
    return prods


def lawrence_option_years():
    """Returns dict of format {year: dead cap if declined}"""
    options = {
        2029: 78.5,
        2030: 74.8,
        2031: 0.0,
    }

    return options


def lawrence_void_years():
    """Returns dict of format {year: cap hit}"""
    voids = {
        2031: 21.0,
    }
    return voids
