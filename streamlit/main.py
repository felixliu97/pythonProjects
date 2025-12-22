import streamlit as st
import pandas as pd
import json
import os
from projects import asx_monitor
from projects import flashcards

# --- Helper Functions ---
def load_data(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, "data", filename)
    with open(filepath, "r") as f:
        return json.load(f)

# --- Load Data ---
profile = load_data("profile.json")
skills = load_data("skills.json")
projects = load_data("projects.json")

# --- Page Config ---
st.set_page_config(
    page_title=f"{profile['name']} - Portfolio",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Section Styling */
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Card Styling */
    .project-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Social Links */
    .social-link {
        margin-right: 15px;
        text-decoration: none;
        font-size: 1.2rem;
    }
    
    /* Experience Timeline Styling */
    .timeline-item {
        border-left: 2px solid #3182ce;
        padding-left: 20px;
        margin-bottom: 20px;
    }
    
    /* Hide Default Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Primary Button Green Styling */
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    div.stButton > button[kind="primary"]:focus {
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://media.licdn.com/dms/image/v2/D5603AQGI3jtiRX8m1g/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1688468011137?e=1767830400&v=beta&t=hTjzT3Eafl9RM14u-YZdVLURNiqIdGzM_wwstIiPpYo", width=150)
st.sidebar.title(profile["name"])
st.sidebar.caption(profile["title"])

st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "active_project" not in st.session_state:
    st.session_state.active_project = None

def set_page(page_name):
    st.session_state.page = page_name
    st.session_state.active_project = None

st.sidebar.button("🏠 Home", on_click=set_page, args=("Home",), use_container_width=True)
st.sidebar.button("🛠️ Skills", on_click=set_page, args=("Skills",), use_container_width=True)
st.sidebar.button("🚀 Projects", on_click=set_page, args=("Projects",), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style='text-align: center;'>
    <a href="{profile['socials']['github']}" class="social-link">GitHub</a>
    <a href="{profile['socials']['linkedin']}" class="social-link">LinkedIn</a>
</div>
""", unsafe_allow_html=True)

# --- Main Content ---
page = st.session_state.page

if page == "Home":
    st.markdown(f"<div class='hero-title'>Hi, I'm {profile['name'].split()[0]} 👋</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hero-subtitle'>{profile['tagline']}</div>", unsafe_allow_html=True)
    st.write(profile["bio"])
    
    st.divider()
    st.subheader("Experience")
    for job in profile["timeline"]:
        # Handle optional description
        desc = job.get('description', '')
        desc_html = f"<br>{desc}" if desc else ""
        
        st.markdown(f"""
        <div class="timeline-item">
            <strong>{job['role']}</strong> @ {job['company']}<br>
            <span style="color: grey; font-size: 0.9em;">{job['year']}</span>
            {desc_html}
        </div>
        """, unsafe_allow_html=True)

elif page == "Skills":
    st.title("🛠️ Skills")
    st.markdown("Here is a breakdown of my technical arsenal.")
    
    for skill_group in skills:
        st.subheader(skill_group["category"])
        
        # Display skills as styled tags
        tags_html = "".join([
            f'<span style="background-color: #e6f3ff; color: #0066cc; padding: 8px 15px; border-radius: 20px; margin-right: 10px; margin-bottom: 10px; display: inline-block; font-size: 0.9em;">{skill}</span>' 
            for skill in skill_group["skills"]
        ])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.write("") # Add some space between categories

elif page == "Projects":
    if st.session_state.active_project == "ASX Stock Monitor":
        if st.button("← Back to Gallery"):
            st.session_state.active_project = None
            st.rerun()

        st.title("📈 ASX Stock Monitor")
        st.markdown("Real-time tracking of 100 ASX blue-chip stocks.")
        
        with st.spinner("Fetching market data... (This may take a moment)"):
            df = asx_monitor.fetch_asx_data()
        
        if not df.empty:
            # Display metrics with styling
            col1, col2, col3 = st.columns(3)
            with col1:
                top_score = df.iloc[0]
                st.metric(
                    label="Top Safe Stock", 
                    value=top_score['Symbol'], 
                    delta=f"{top_score['Score']} Score",
                    help="Stock with the highest combined safety and performance score"
                )
            with col2:
                top_gainer = df.loc[df['1D Change'].idxmax()]
                st.metric(
                    label="Top Gainer (1D)", 
                    value=top_gainer['Symbol'], 
                    delta=f"{top_gainer['1D Change']:.2f}%"
                )
            with col3:
               top_mom = df.loc[df['Momentum'].idxmax()]
               st.metric(
                   label="Highest Momentum", 
                   value=top_mom['Symbol'], 
                   delta=f"{top_mom['Momentum']:.2f}%",
                   help="Stock with the strongest 5-day price trend"
               )

            st.divider()

            # Prepare Dataframe for display
            df_display = df.copy()

            # --- Formatting for Native Dataframe ---
            # Keep numeric values for sorting, but scale large numbers
            df_display['MC'] = df_display['MC'] / 1e9  # Convert to Billions

            # Select and Rename Columns
            cols_to_show = ["Symbol", "Name", "Industry", "MC", "Price", "PE", "PS", "Score", "1D Change", "5D Change", "Momentum", "Volatility", "RSI"]
            df_final = df_display[cols_to_show].copy()

            # --- Styling API ---
            # Apply color mapping (Green/Red)
            def color_change(val):
                try:
                    v = float(val)
                    if v > 0: return 'color: #28a745'
                    if v < 0: return 'color: #dc3545'
                except: pass
                return ''
            
            def color_rsi(val):
                try:
                    v = float(val)
                    if v >= 70: return 'color: #dc3545; font-weight: bold'
                    if v <= 30: return 'color: #28a745; font-weight: bold'
                except: pass
                return ''

            styler = df_final.style.map(color_change, subset=['1D Change', '5D Change', 'Momentum'])\
                                   .map(color_rsi, subset=['RSI'])\
                                   .format({
                                       "PE": "{:.1f}", 
                                       "PS": "{:.2f}", 
                                       "RSI": "{:.1f}",
                                       "Score": "{:.0f}"
                                   })

            # --- Column Configurations ---
            column_config = {
                "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Industry": st.column_config.TextColumn("Industry", width="medium"),
                "MC": st.column_config.NumberColumn(
                    "Market Cap",
                    help="Market Capitalization in Billions",
                    format="$%.2f B",
                    min_value=0,
                ),
                "Price": st.column_config.NumberColumn(
                    "Price",
                    format="$%.2f",
                ),
                "PE": st.column_config.NumberColumn("P/E", help="Price to Earnings Ratio"),
                "PS": st.column_config.NumberColumn("P/S", help="Price to Sales Ratio"),
                "Score": st.column_config.NumberColumn(
                    "Score", 
                    help="Composite Safety & Performance Score (0-100)",
                    format="%.0f"
                ),
                "1D Change": st.column_config.NumberColumn("1D Chg", format="%+.2f%%"),
                "5D Change": st.column_config.NumberColumn("5D Chg", format="%+.2f%%"),
                "Momentum": st.column_config.NumberColumn("Momentum", format="%+.2f%%"),
                "Volatility": st.column_config.NumberColumn("Volatility", format="%.2f%%"),
                "RSI": st.column_config.NumberColumn("RSI", help="Relative Strength Index (14d)"),
            }

            # Render Native Dataframe
            st.dataframe(
                styler,
                column_config=column_config,
                width="stretch",
                hide_index=True,
                height=600
            )

            # --- Market Insights ---
            st.divider()
            st.subheader("💡 Market Insights")
            
            # Top Gainers/Losers
            gainers = df.nlargest(3, '1D Change')
            losers = df.nsmallest(3, '1D Change')
            
            c1, c2 = st.columns(2)
            with c1:
                st.caption("🚀 Top Movers (24h)")
                for _, row in gainers.iterrows():
                     st.markdown(f"<div style='display:flex; justify-content:space-between'><b>{row['Symbol']}</b> <span style='color:#28a745'>+{row['1D Change']:.2f}%</span></div>", unsafe_allow_html=True)
            with c2:
                st.caption("🔻 Top Decliners (24h)")
                for _, row in losers.iterrows():
                     st.markdown(f"<div style='display:flex; justify-content:space-between'><b>{row['Symbol']}</b> <span style='color:#dc3545'>{row['1D Change']:.2f}%</span></div>", unsafe_allow_html=True)

            st.write("")
            
            # RSI Alerts (Compact Pills)
            overbought = df[df['RSI'] >= 70]
            oversold = df[df['RSI'] <= 30]

            if not overbought.empty or not oversold.empty:
                st.caption("⚠️ RSI Alerts")
                
                if not overbought.empty:
                    st.markdown("**Overbought (>70):** " + " ".join([
                        f"<span style='background-color:rgba(220,53,69,0.2); color:#dc3545; padding:2px 8px; border-radius:12px; font-size:0.9em; margin-right:5px; display:inline-block'><b>{row['Symbol']}</b> {row['RSI']:.1f}</span>" 
                        for _, row in overbought.iterrows()
                    ]), unsafe_allow_html=True)
                
                if not oversold.empty:
                    st.markdown("**Oversold (<30):** " + " ".join([
                        f"<span style='background-color:rgba(40,167,69,0.2); color:#28a745; padding:2px 8px; border-radius:12px; font-size:0.9em; margin-right:5px; display:inline-block'><b>{row['Symbol']}</b> {row['RSI']:.1f}</span>" 
                        for _, row in oversold.iterrows()
                    ]), unsafe_allow_html=True)
            else:
                 st.caption("All stocks are currently within neutral RSI levels (30-70).")
        else:
            st.error("Failed to fetch data. Please try again later.")

    elif st.session_state.active_project == "AI Flashcard Generator":
        flashcards.render_flashcard_generator()
    else:
        # Standard Projects Gallery
        st.title("🚀 Project Gallery")
        st.markdown("A selection of my recent work.")
        
        # Filter
        all_categories = ["All"] + list(set([p["category"] for p in projects]))
        selected_cat = st.selectbox("Filter by Category", all_categories)
        
        filtered_projects = projects if selected_cat == "All" else [p for p in projects if p["category"] == selected_cat]
        
        # Grid Layout
        cols = st.columns(2)
        
        def set_active_project(project_title):
            st.session_state.active_project = project_title
        
        for idx, project in enumerate(filtered_projects):
            with cols[idx % 2]:
                with st.container():
                    # Handle local images vs remote URLs
                    image_path = project["image"]
                    if not image_path.startswith("http") and not os.path.isabs(image_path):
                        image_path = os.path.join(os.path.dirname(__file__), image_path)
                    
                    st.image(image_path, use_container_width=True)
                    st.subheader(project["title"])
                    st.caption(f"{project['category']} | {' • '.join(project['tags'])}")
                    st.write(project["description"])
                    
                    if project["demo"].startswith("internal:"):
                            st.button("Try it Live", key=f"btn_demo_{idx}", type="primary", on_click=set_active_project, args=(project["title"],))
                    else:
                            st.link_button("Live Demo", project["demo"])
                    st.divider()

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>© 2025 {profile['name']}. Built with Streamlit & Python.</div>", unsafe_allow_html=True)