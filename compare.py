from contract import ContractEvaluation, Contract
from scipy.optimize import minimize


def zero_surplus_value(prod: float, ct: Contract):
    prods = [prod[0] for _ in ct.seasons]
    eval_ct = ContractEvaluation(ct, prods, "")
    surplus_value = eval_ct.evaluate()
    return abs(0 - surplus_value)


def find_breakeven_point(ct: Contract) -> int:
    """
    Finds the minimum average QBR a QB would have to produce in
    order to return positive value on the contract
    """
    prod = minimize(zero_surplus_value, [50], args=(ct,), tol=1.0)
    breakeven_point = int(prod.x[0])
    return breakeven_point


def find_option_tender_avg(ct: ContractEvaluation) -> int:
    """
    Finds the average QBR a QB would have to produce in
    order to make it worth tendering ALL option years
    """
    pass


def find_option_tender_season(ct: ContractEvaluation) -> int:
    """
    Finds the QBR by year a QB would have to produce in
    order to make it worth tendering ALL option years
    """
    pass
