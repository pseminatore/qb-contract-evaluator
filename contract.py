class Contract():
    seasons: list = []
    
    
    def __init__(self, seasons, salaries, options, voids) -> None:
        self.seasons = seasons
        self.salaries = salaries
        self.options = options
        self.voids = voids
        
        
    def option_years(self) -> list:
        return self.options.keys()
    
    def option_dead_cap(self) -> list:
        return self.options.values()
    
    def void_years(self) -> list:
        return self.voids.keys()
    
    def void_dead_cap(self) -> list:
        return self.voids.values()
    
    
class ContractSeason():
    year: int
    is_option_year: bool
    is_void_year: bool
    base_salary: bool
    option_salary: float
    option_dead_cap: float
    void_dead_cap: float
    
    def __init__(self, year, is_option_year, is_void_year, base_salary, option_salary, option_dead_cap, void_dead_cap) -> None:
        pass
    