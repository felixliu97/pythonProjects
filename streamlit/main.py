import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Config
st.set_page_config(
    page_title="Streamlit Modern UI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS for "Nice UI"
st.markdown("""
<style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Card Styling */
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #0e1117;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #fafafa;
    }
    
    /* Hide Default Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("Explore the app sections below.")

tab_list = ['Home', 'Resources', 'Gallery', 'Vision', 'About']
icons = ['🏠', '📚', '🖼️', '👁️', '👤']

if "tab_index" not in st.session_state:
    st.session_state.tab_index = 0

def next_tab():
    st.session_state.tab_index = (st.session_state.tab_index + 1) % len(tab_list)

# Navigation Menu
selected_tab = st.sidebar.radio(
    "Go to",
    tab_list,
    index=st.session_state.tab_index,
    format_func=lambda x: f"{icons[tab_list.index(x)]} {x}"
)

# Update session state if radio changes (optional sync)
st.session_state.tab_index = tab_list.index(selected_tab)

st.sidebar.markdown("---")
st.sidebar.button('Next Page ➡️', on_click=next_tab, use_container_width=True)


# 4. Main Content Area
if selected_tab == 'Home':
    st.title("🏠 Dashboard Home")
    st.markdown("Welcome to the **Modern Streamlit Dashboard**. Here is an overview of your key metrics.")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", "1,234", "+5%")
    with col2:
        st.metric("Revenue", "$12,345", "+12%")
    with col3:
        st.metric("Conversion", "3.2%", "-0.5%")
    with col4:
        st.metric("Active Sessions", "456", "+18%")
        
    st.markdown("### 📈 Performance Trend")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['a', 'b', 'c']
    )
    st.area_chart(chart_data)

elif selected_tab == 'Resources':
    st.title("📚 Resources")
    st.markdown("Access helpful documentation and external links.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("**Documentation**\n\nRead the full docs to get started.")
        st.markdown("[View Docs >](#)")
    with c2:
        st.success("**API Reference**\n\nEndpoints and usage examples.")
        st.markdown("[View API >](#)")
        
    st.markdown("### Downloads")
    data = pd.DataFrame({'File': ['Report_Q1.pdf', 'Data_Summary.csv'], 'Size': ['1.2 MB', '450 KB']})
    st.table(data)

elif selected_tab == 'Gallery':
    st.title("🖼️ Gallery")
    st.markdown("A collection of visuals and placeholders.")
    
    # Masonry-like grid
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://picsum.photos/300/200", caption="Project Alpha", use_column_width=True)
        st.image("https://picsum.photos/300/300", caption="Team Event", use_column_width=True)
    with c2:
        st.image("https://picsum.photos/300/250", caption="Design Mockup", use_column_width=True)
        st.image("https://picsum.photos/300/200", caption="Architecture", use_column_width=True)
    with c3:
        st.image("https://picsum.photos/300/300", caption="Product Launch", use_column_width=True)
        st.image("https://picsum.photos/300/250", caption="Analytics", use_column_width=True)

elif selected_tab == 'Vision':
    st.title("👁️ The Vision")
    
    st.markdown("""
    > "To empower every developer to build beautiful data apps in minutes."
    
    ### Our Mission
    We believe in **simplicity**, **speed**, and **aesthetics**. Our goal is to reduce the barrier to entry for creates of all backgrounds.
    
    ### Road Map
    - [x] Phase 1: MVP
    - [ ] Phase 2: Enhanced UI
    - [ ] Phase 3: Global Scale
    """)

elif selected_tab == 'About':
    st.title("👤 About Us")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=150)
    with col2:
        st.subheader("Felix Liu")
        st.caption("Lead Developer")
        st.write("Passionate about Python, AI, and building clean user interfaces.")
        st.markdown("[GitHub](https://github.com) | [Twitter](https://twitter.com)")
    
    st.divider()
    st.caption("© 2025 Streamlit Modern App. All rights reserved.")