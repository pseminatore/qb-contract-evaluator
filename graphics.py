import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as colors
import os
import pandas as pd
from value import get_apy_prod_value_6_poly

    
def plot_market_value_curve(prod_func=get_apy_prod_value_6_poly):
    prods = [x for x in range(0, 101)]
    values = [prod_func(prod) for prod in prods]
    fig = px.scatter(x=prods, y=values)
    fig.show()
    
    
def cost_per_production_trend():
    seasons = [20, 21, 22, 23, 18, 19, 23, 21, 20, 23]
    cpw = [0.62, 0.65, 0.86, 0.81, 0.45, 0.58, 0.93, 0.75, 0.72, 0.75]
    fig = px.scatter(x=seasons, y=cpw, trendline='ols')
    fig.show()
    
    
def build_surplus_value_graphic(leaderboard, surplus_value, player_name, option_year=None, void_year=None, save_show=False):
    fig = go.Figure()
    leaderboard = pd.DataFrame(leaderboard)
    leaderboard.rename(columns={'QBR': 'Proj. QBR', 'Market Sal': 'Market Sal. ($M)', 'Actual Sal': 'Actual Sal. ($M)', 'Tot. Surplus Value': 'Surplus Value ($M)'}, inplace=True)
    header_cols = [col for col in leaderboard.columns if col not in ['border_color', 'border_size', 'Option Sal', 'Void Sal']]
    normalized_colorpoints = (leaderboard['Surplus Value ($M)'] + 70) / 140
    colors_arr = colors.sample_colorscale('RdBu_r', normalized_colorpoints, low=0, high=1.0)
    leaderboard['border_color'] = ['rgb(217, 173, 28)' if (szn is not None and void_year is not None) and szn >= void_year else 'rgb(40, 161, 66)' if option_year is not None and szn >= option_year else 'grey' for szn in leaderboard['Season'].to_list()]
    leaderboard['border_size'] = [5 if szn in [option_year, void_year] or (void_year is not None and szn > void_year) else 1 for szn in leaderboard['Season'].to_list() ]
    fill_colors = ['rgb(237,237,237)' for _ in range(len(header_cols) - 1)] + [colors_arr]
    line_widths = []
    for _ in header_cols:
        for season in leaderboard['Season']:
            width = 5 if (option_year is not None and season >= option_year) or (void_year is not None  and season >= void_year) else 1
            line_widths.append(width)
            
    title = f"Surplus Value Breakdown"
    surplus_value_str = f"Contract Surplus Value: "
    surplus_value_amount = f"${surplus_value:.01f}"
    surplus_value_str_color = 'rgb(50, 168, 60)' if surplus_value > 0 else 'rgb(168, 50, 60)'
    fig.add_annotation(xref="x domain",yref="paper",x=0.5, y=1.025, showarrow=False,
                text=title, font=dict(size=42))
    fig.add_annotation(xref="x domain",yref="paper",x=0.5, y=0.9975, showarrow=False,
                text=player_name, font=dict(size=38))
    fig.add_annotation(xref="x domain",yref="paper",x=0.4, y=0.975, showarrow=False,
                text=surplus_value_str, font=dict(size=38))
    fig.add_annotation(xref="x domain",yref="paper",x=0.785, y=0.975, showarrow=False,
                text=surplus_value_amount, font=dict(size=38, color=surplus_value_str_color))
    fig.add_annotation(xref="x domain",yref="y domain",x=0.05, y=0.58, showarrow=False,
                text="Green: Option Year", font=dict(size=24, color='rgb(40, 161, 66)'))
    fig.add_annotation(xref="x domain",yref="y domain",x=0.05, y=0.56, showarrow=False,
                text="Yellow: Void Year", font=dict(size=24, color='rgb(217, 173, 28)'))
    fig.add_trace(go.Table(
        header=dict(values=header_cols, height=56, font=dict(size=39)),
        cells=dict(values=[leaderboard['Season'], leaderboard['Proj. QBR'], round(leaderboard['Market Sal. ($M)'], 1), round(leaderboard['Actual Sal. ($M)'], 1), round(leaderboard['Inflation Adj'], 3), round(leaderboard['Surplus Value ($M)'], 1)], height=55, font=dict(size=38), fill_color=fill_colors, line_color=[leaderboard['border_color']], line_width=leaderboard['border_size'].to_list(), prefix=['', '', '$', '$', '', '$']),
        domain=dict(y=[0, 0.92])
    ))
    fig.update_layout(
        width=1080,
        height=2000,
        template='ggplot2',
    ) 
    if save_show:
        fig.show()
    else:
        if not os.path.exists(f"outputs/contract_breakdowns"):
            os.mkdir(f"outputs/contract_breakdowns")
        fig.write_image(f"outputs/contract_breakdowns/{player_name}.png")
    return