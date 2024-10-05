def salary_cousins_actual(season):
    cap_salaries = {
        2024: 25.0,
        2025: 40.0,
        2026: 57.5,
        2027: 57.5, 
    }
    return cap_salaries.get(season, 0.0)

def salary_penix_actual(season):
    cap_salaries = {
        2024: 4.1,
        2025: 5.2,
        2026: 6.2,
        2027: 7.3,
        2028: 25.0
    }
    return cap_salaries.get(season, 0.0)

def cost_per_win_qb(season):
    season = season - 2000
    cpw = (0.0710714 * season) - 0.7805
    return cpw