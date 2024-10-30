# qb_contract_evaluator
A python package for working with and evaluating NFL Quarterback contract value.  This package uses a proprietary valuation model to assign a dollar value to QBR, an aggregated measure of production developed by [ESPN](https://www.espn.com/nfl/story/_/id/17653521/how-total-qbr-calculated-explain-our-improved-qb-rating).




## Usage

```python
from qb_contract_evaluator import contract
```

### Defining a Contract
A `Contract` represents just that - an uncontextualized representation of money distributed over a number of years. A `Contract` itself has no inherent value, and is purely a structured collection of information.  While in reality, NFL contracts can have all sorts of clauses, bonuses, and options, this project aims to keep things simple.  Seasons can be one of three types: Guaranteed, Option, or Void.  Each dollar value assigned to a season should represent the Cap Number for that year of the contract.  More information on how the Cap Number is calculated can be found [here](https://bleacherreport.com/articles/1665623-how-does-the-salary-cap-work-in-the-nfl).  `Contract` objects can be constructed via shorthand initialization, or via long-form records.

**Creating a Contract by Initialization**

Here we will use Dak Prescott's current contract as an example:

```python
from qb_contract_evaluator.contract import Contract

prescott_ct = Contract(
        start_year=2024,
        end_year=2028,
        salaries=[43.4, 89.9, 68.0, 62.0, 0.0],
        option_year=2028,
        option_salaries=[72.0],
        option_dead_caps=[34.0],
        void_year=None,
        void_dead_caps=None
    )
```

**Creating a Contract from Records**

Here we will use Trevor Lawrence's current contract as an example:

```python
from qb_contract_evaluator.contract import Contract
 
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
lawrence_ct = Contract().from_records(dt)
```
**Viewing a Contract Breakdown**

To visualize a `Contract`'s structure, a string representation of the `Contract` can simply be printed

```python
print(lawrence_ct)
```
```
>>>
  Season    Base Sal  Option Sal    Void Sal
--------  ----------  ------------  ----------
    2024          15  --            --
    2025          17  --            --
    2026          24  --            --
    2027          35  --            --
    2028          47  --            --
    2029           0  78.5          --
    2030           0  74.8          --
    2031           0  --            21.0
```

### Defining a ContractEvaluation
A `ContractEvaluation` object represents a contextualized version of a `Contract`. It contains all of the financial information that the underlying `Contract` has, but is assigned to a specific player and by providing a player's production (QBR), it can be assigned a specific dollar value.  

**Creating a ContractEvaluation from a Contract**

As an extension of a `Contract`, a `ContractEvaluation` can be instantiated simply by providing a base contract and player context.  Here, we will continue to use Trevor Lawrence as an example:

```python
from qb_contract_evaluator.contract import ContractEvaluation

production = [
        56,
        57,
        59,
        59,
        57,
        57,
        56,
        0, # Since 2031 is a Void year, Lawrence will generate 0.0 QBR
    ]
eval_ct = ContractEvaluation(ct, production, player_name="Trevor Lawrence")
```

**Evaluating a ContractEvaluation**

Evaluating a `ContractEvaluation` will generate a Market Value, Total Value, and Surplus Value, as well as determining which Option years will be tendered or declined.
```python
surplus_value = eval_ct.evaluate()
```
```
>>> 44.0
```

**Viewing a ContractEvaluation breakdown**
Similar to a `Contract`, a string representation of a `ContractEvaluation` can be printed.  This function will also call `evaluate()` if it hasn't been evaluated already.

```python
print(eval_ct)
```
```
>>>
  Season    QBR    Market Sal    Actual Sal    Inflation Adj    Tot. Surplus Value  Option Sal    Void Sal
--------  -----  ------------  ------------  ---------------  --------------------  ------------  ----------
    2024     56       31.409             15          1                    16.409    --            --
    2025     57       35.9205            17          1.0858               18.9205   --            --
    2026     59       43.0161            24          1.17896              19.0161   --            --
    2027     59       46.7069            35          1.28012              11.7069   --            --
    2028     57       45.9824            47          1.38995              -1.01755  --            --
    2029      0        0                  0          1.50921               0        78.5          --
    2030      0        0                  0          1.6387                0        74.8          --
    2031      0        0                 21          1.7793              -21        --            21.0
```

**Generating a ContractEvaluation breakdown graphic**

`ContractEvaluations` can generate a PNG representation of the contract value using Plotly[insert link].  By default, these images are saved to a `./outputs/contract_breakdowns/` folder.  However, there is an option to display the image in the browser instead.

```python
eval_ct.build_surplus_value_graphic()
```
![breakdownImage](./outputs/contract_breakdowns/Trevor%20Lawrence.png)

To display in the browser, set the `save_show` flag to `True`
```python
eval_ct.build_surplus_value_graphic(save_show=True)
```
## Recognition

The raw financial data behind all of these evaluations comes via [Spotrac](https://www.spotrac.com/) and [OverTheCap](https://overthecap.com/).  QBR comes from [ESPN](https://www.espn.com/)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
