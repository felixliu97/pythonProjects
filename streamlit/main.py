import streamlit as st
import pandas as pd
import json
import os
import requests
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
            
            # --- Sorting Logic Removed (Handled by JS now) ---

            # --- Formatting for HTML Table ---
            # Apply formatting programmatically since we are converting to HTML
            df_display['MC'] = (df_display['MC'] / 1e9).map('${:,.2f} B'.format)
            df_display['Price'] = df_display['Price'].map('${:,.2f}'.format)
            df_display['PE'] = df_display['PE'].map('{:.1f}'.format)
            df_display['PS'] = df_display['PS'].map('{:.2f}'.format)
            df_display['1D Change'] = df_display['1D Change'].map('{:+.2f}%'.format)
            df_display['5D Change'] = df_display['5D Change'].map('{:+.2f}%'.format)
            df_display['Momentum'] = df_display['Momentum'].map('{:+.2f}%'.format)
            df_display['Volatility'] = df_display['Volatility'].map('{:.2f}%'.format)
            df_display['RSI'] = df_display['RSI'].map('{:.1f}'.format)
            df_display['Score'] = df_display['Score'].map('{:.0f}'.format)

            # Select and Rename Columns
            cols_to_show = ["Symbol", "Name", "Industry", "MC", "Price", "PE", "PS", "Score", "1D Change", "5D Change", "Momentum", "Volatility", "RSI"]
            df_final = df_display[cols_to_show].copy()

            # --- Styling API ---
            def color_change_html(val):
                if '+' in val: return 'color: #28a745'
                if '-' in val: return 'color: #dc3545'
                return ''
            
            def color_rsi_html(val):
                try:
                    v = float(val)
                    if v >= 70: return 'color: #dc3545; font-weight: bold'
                    if v <= 30: return 'color: #28a745; font-weight: bold'
                except: pass
                return ''

            styler = df_final.style.map(color_change_html, subset=['1D Change', '5D Change', 'Momentum'])\
                                   .map(color_rsi_html, subset=['RSI'])\
                                   .hide(axis="index")

            # Render HTML with pandas
            html_table = styler.to_html(table_id="asx-table")
            # Inject Header Click Events directly into HTML for reliability
            import re
            
            # 1. Force ID to "asx-table" to ensure JS and CSS target it correctly
            # Remove any existing id attributes from the table tag and simple force our own
            html_table = re.sub(r'<table[^>]*>', '<table id="asx-table">', html_table, count=1)
            
            # 2. Inject onclick handlers for sorting
            # Matches <th class="..."> or <th>
            html_table = re.sub(
                r'<th(\s+[^>]*)?>', 
                r'<th\1 onclick="sortTable(this.cellIndex, \'asx-table\')" style="cursor:pointer" title="Click to sort">', 
                html_table
            )
            
            # Custom CSS for Sticky Header and Colors
            custom_css = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
                body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
                table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; font-size: 0.9rem; }
                thead th { 
                    background-color: #0066cc !important; 
                    color: white !important; 
                    position: sticky; top: 0; z-index: 100;
                    padding: 12px; text-align: left;
                    cursor: pointer;
                }
                thead th:hover { background-color: #0056b3 !important; }
                tbody td { padding: 8px 12px; border-bottom: 1px solid #ddd; }
                tbody tr:nth-child(even) { background-color: #f2f2f2; }
                tbody tr:hover { background-color: #e6e6e6; transition: background 0.2s; }
            </style>
            """

            # JS for Sorting (Adapted from asx_report reference)
            sort_script = """
            <script>
            function sortTable(n, tableId) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById(tableId);
                if (!table) return;
                
                switching = true; dir = "asc"; 
                
                function parseMoney(str) {
                    if (!str) return -1;
                    var clean = str.replace(/[$,]/g, "").trim();
                    var mult = 1;
                    if (clean.endsWith("B")) { mult = 1e9; clean = clean.slice(0, -1); }
                    else if (clean.endsWith("M")) { mult = 1e6; clean = clean.slice(0, -1); }
                    else if (clean.endsWith("K")) { mult = 1e3; clean = clean.slice(0, -1); }
                    else if (clean.endsWith("%")) { clean = clean.slice(0, -1); }
                    
                    var val = parseFloat(clean);
                    if (isNaN(val)) return -999999;
                    return val * mult;
                }

                while (switching) {
                    switching = false; 
                    rows = table.rows;
                    // Try to identify body rows. Pandas `to_html` typically outputs <thead> and <tbody>.
                    // If <tbody> exists, use it.
                    var body = table.tBodies[0];
                    var bodyRows = body ? body.rows : rows; 
                    
                    // If using rows directly, we need to skip header. 
                    // If using tBodies[0], it usually contains only data rows.
                    // Let's assume tBodies[0] is safe as pandas generates it.
                    
                    for (i = 0; i < (bodyRows.length - 1); i++) {
                        shouldSwitch = false;
                        x = bodyRows[i].getElementsByTagName("TD")[n];
                        y = bodyRows[i + 1].getElementsByTagName("TD")[n];
                        
                        var xContent = x.textContent.trim();
                        var yContent = y.textContent.trim();
                        
                        var xVal = parseMoney(xContent);
                        var yVal = parseMoney(yContent);
                        
                        if (xVal !== -999999 && yVal !== -999999) {
                            if (dir == "asc") { if (xVal > yVal) { shouldSwitch = true; break; } }
                            else { if (xVal < yVal) { shouldSwitch = true; break; } }
                        } else {
                            if (dir == "asc") { if (xContent.toLowerCase() > yContent.toLowerCase()) { shouldSwitch = true; break; } }
                            else { if (xContent.toLowerCase() < yContent.toLowerCase()) { shouldSwitch = true; break; } }
                        }
                    }
                    if (shouldSwitch) {
                        bodyRows[i].parentNode.insertBefore(bodyRows[i + 1], bodyRows[i]);
                        switching = true; switchcount ++; 
                    } else {
                        if (switchcount == 0 && dir == "asc") { dir = "desc"; switching = true; }
                    }
                }
            }
            </script>
            """
            
            # Wrap in full HTML structure for the component
            full_html = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    {custom_css}
                    {sort_script}
                </head>
                <body>
                    {html_table}
                </body>
            </html>
            """
            
            import streamlit.components.v1 as components
            components.html(full_html, height=600, scrolling=True)

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