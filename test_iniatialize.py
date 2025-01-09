from sample_contracts import lawrence_info, production_curve_lawrence
from contract import Contract, ContractEvaluation


# def test_contract():
#     is_success = True
#     try:
#         ct = Contract().from_records(lawrence_info())
#     except Exception as e:
#         print(e)
#         is_success = False
#     assert is_success == True


def test_contract_evaluation():
    is_success = True
    try:
        ct = Contract().from_records(lawrence_info())
        ct_eval = ContractEvaluation(ct, production_curve_lawrence())
    except Exception as e:
        print(e)
        is_success = False
    assert is_success == True


def test_contract_breakdown():
    tcb_ct = Contract().from_records(lawrence_info())
    tcb_ct_eval = ContractEvaluation(tcb_ct, production_curve_lawrence())
    tcb_contract_value = tcb_ct_eval.generate_breakdown()
    assert tcb_ct_eval.breakdown is not None


if __name__ == "__main__":
    test_contract_breakdown()
