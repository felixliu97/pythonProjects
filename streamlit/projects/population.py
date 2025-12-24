import streamlit as st
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import uuid
import os

def render_population_animation():
    st.title("🌍 Population Over Time")
    st.markdown("A dynamic visualization of the world's most populous countries (1960-2024).")
    
    @st.cache_data
    def get_population_dataset():
        # Load from CSV
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'population_data.csv')
        if not os.path.exists(csv_path):
            st.error("Data not found. Please run the data fetcher.")
            return pd.DataFrame()
            
        df = pd.read_csv(csv_path)
        
        # Ensure year is int
        df['year'] = df['year'].astype(int)
        
        # NOTE: Continent logic is now baked into the CSV generation (rebuild_population_data.py)
        # We just read the 'continent' column.
        if 'continent' not in df.columns:
            # Fallback if old CSV
            st.warning("Continent data missing from CSV. Please regenerate data.")
            df['continent'] = 'Other'

        # 1. Ranking per year
        df['rank'] = df.groupby('year')['pop'].rank(ascending=False, method='first')
        
        # Filter top 15
        df_top15 = df[df['rank'] <= 15].copy()
        
        # Format Labels
        def fmt_pop(x):
            if pd.isna(x): return ""
            return f"{x/1e6:.0f}M" if x < 1e9 else f"{x/1e9:.2f}B"
            
        df_top15['pop_display'] = df_top15['pop'].apply(fmt_pop)
        
        df_top15['inv_rank'] = -df_top15['rank']
        
        # Continent Colors
        continent_map = {
            'Asia': '#636EFA',          # Blue
            'Africa': '#00CC96',        # Green
            'North America': '#FFA15A', # Orange
            'South America': '#AB63FA', # Purple
            'Antarctica': '#D3D3D3',    # Grey
            'Europe': '#EF553B',        # Red
            'Oceania': '#19D3F3',       # Cyan
        }
        # Fallback color
        df_top15['color'] = df_top15['continent'].map(continent_map).fillna('#B6E880')
        
        # Sort by Rank (1 to 15)
        df_top15 = df_top15.sort_values(['year', 'rank'])
        return df_top15, continent_map

    result = get_population_dataset()
    
    if isinstance(result, tuple):
        df_dataset, continent_map = result
    else:
        return

    if df_dataset.empty:
        return

    # Define Layout
    max_pop = df_dataset['pop'].max() * 1.25 
    
    initial_year = df_dataset['year'].min()
    years = sorted(df_dataset['year'].unique())
    current_year = df_dataset['year'].max()

    layout_settings = dict(
        xaxis_title="Population",
        yaxis_title=None, 
        xaxis=dict(
            showgrid=True, 
            fixedrange=True,
            range=[0, max_pop],
            side='bottom' 
        ),
        yaxis=dict(
            showgrid=False, 
            fixedrange=True,
            autorange="reversed" 
        ),
        height=700,
        margin=dict(l=150, r=200, t=100, b=50),
        title=dict(
            text=str(initial_year),
            y=0.95,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=60, color="#555555")
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    # Build Frames
    frames = []
    for year in years:
        frame_data = df_dataset[df_dataset['year'] == year]
        frame_data = frame_data.sort_values('rank')
        
        frames.append(go.Frame(
            data=[go.Bar(
                x=frame_data['pop'],              
                y=frame_data['country'].tolist(), 
                orientation='h',                  
                text=frame_data['pop_display'],   
                textposition='outside',           
                marker=dict(color=frame_data['color']),
                showlegend=False
            )],
            layout=go.Layout(
                title_text=str(year),
                yaxis=dict(
                    type='category',
                    categoryorder='array',
                    categoryarray=frame_data['country'].tolist()
                )
            ),
            name=str(year)
        ))

    # Initial Data
    initial_data = df_dataset[df_dataset['year'] == initial_year]
    initial_data = initial_data.sort_values('rank')
    
    # Create Legend Traces
    legend_traces = []
    # Sorted order for consistent legend
    ordered_continents = ['Asia', 'Africa', 'North America', 'South America', 'Antarctica', 'Europe', 'Oceania']
    
    for continent in ordered_continents:
        if continent in continent_map:
            color = continent_map[continent]
            legend_traces.append(go.Bar(
                name=continent,
                x=[None],
                y=[None],
                marker=dict(color=color),
                showlegend=True,
                hoverinfo='none'
            ))

    # Fix: Put Main Bar Trace FIRST to align with animation frames
    fig = go.Figure(
        data=[go.Bar(
            x=initial_data['pop'],
            y=initial_data['country'].tolist(),
            orientation='h',
            text=initial_data['pop_display'],
            textposition='outside',
            marker=dict(color=initial_data['color']),
            showlegend=False
        )] + legend_traces,
        layout=layout_settings,
        frames=frames
    )
    
    # Initialize Y-axis order
    fig.update_layout(yaxis=dict(
        categoryorder='array',
        categoryarray=initial_data['country'].tolist()
    ))

    # Generate Unique ID for Autoplay
    plot_div_id = "population_chart_v" + str(uuid.uuid4())
    
    # Generate HTML
    config = {'displayModeBar': False}
    graph_html = pio.to_html(fig, config=config, include_plotlyjs='cdn', full_html=True, div_id=plot_div_id)
    
    # Autoplay Script
    autoplay_script = f"""
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var attempts = 0;
            var interval = setInterval(function() {{
                var plot = document.getElementById('{plot_div_id}');
                if (plot) {{
                    Plotly.animate(plot, null, {{
                        mode: 'immediate', 
                        fromcurrent: true, 
                        transition: {{duration: 500, easing: 'cubic-in-out'}}, 
                        frame: {{duration: 1000, redraw: true}}
                    }});
                    clearInterval(interval);
                }}
                attempts++;
                if (attempts > 20) clearInterval(interval);
            }}, 500);
        }});
    </script>
    """
    
    html_with_autoplay = graph_html.replace('</body>', autoplay_script + '</body>')
    
    components.html(html_with_autoplay, height=750, width=1100)
