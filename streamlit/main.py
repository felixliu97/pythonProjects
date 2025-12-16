import streamlit as st
import pandas as pd
import json
import os

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
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", width=150)
st.sidebar.title(profile["name"])
st.sidebar.caption(profile["title"])

st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "About"

def set_page(page_name):
    st.session_state.page = page_name

st.sidebar.button("👤 About Me", on_click=set_page, args=("About",), use_container_width=True)
st.sidebar.button("🛠️ Skills", on_click=set_page, args=("Skills",), use_container_width=True)
st.sidebar.button("🚀 Projects", on_click=set_page, args=("Projects",), use_container_width=True)
st.sidebar.button("📬 Contact", on_click=set_page, args=("Contact",), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style='text-align: center;'>
    <a href="{profile['socials']['github']}" class="social-link">GitHub</a>
    <a href="{profile['socials']['linkedin']}" class="social-link">LinkedIn</a>
    <a href="{profile['socials']['twitter']}" class="social-link">Twitter</a>
</div>
""", unsafe_allow_html=True)

# --- Main Content ---
page = st.session_state.page

if page == "About":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"<div class='hero-title'>Hi, I'm {profile['name'].split()[0]} 👋</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='hero-subtitle'>{profile['tagline']}</div>", unsafe_allow_html=True)
        st.write(profile["bio"])
        
        st.divider()
        st.subheader("Experience")
        for job in profile["timeline"]:
            st.markdown(f"""
            <div class="timeline-item">
                <strong>{job['role']}</strong> @ {job['company']}<br>
                <span style="color: grey; font-size: 0.9em;">{job['year']}</span><br>
                {job['description']}
            </div>
            """, unsafe_allow_html=True)
            
    with col2:
        # Placeholder for 3D element or illustration
        st.image("https://picsum.photos/400/600", caption="Creating the future", use_column_width=True)

elif page == "Skills":
    st.title("🛠️ Skills & Expertise")
    st.markdown("Here is a breakdown of my technical arsenal.")
    
    df_skills = pd.DataFrame(skills)
    
    # Categorize skills
    categories = df_skills["category"].unique()
    
    for cat in categories:
        st.subheader(cat)
        cat_skills = df_skills[df_skills["category"] == cat]
        
        cols = st.columns(len(cat_skills))
        for idx, (_, skill) in enumerate(cat_skills.iterrows()):
            with cols[idx]:
                st.metric(label=skill["name"], value=f"{skill['level']}%")
                st.progress(skill["level"])

elif page == "Projects":
    st.title("🚀 Project Gallery")
    st.markdown("A selection of my recent work.")
    
    # Filter
    all_categories = ["All"] + list(set([p["category"] for p in projects]))
    selected_cat = st.selectbox("Filter by Category", all_categories)
    
    filtered_projects = projects if selected_cat == "All" else [p for p in projects if p["category"] == selected_cat]
    
    # Grid Layout
    cols = st.columns(2)
    for idx, project in enumerate(filtered_projects):
        with cols[idx % 2]:
            with st.container():
                st.image(project["image"], use_column_width=True)
                st.subheader(project["title"])
                st.caption(f"{project['category']} | {' • '.join(project['tags'])}")
                st.write(project["description"])
                
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("View Code", project["github"], use_container_width=True)
                with c2:
                    st.link_button("Live Demo", project["demo"], use_container_width=True)
                st.divider()

elif page == "Contact":
    st.title("📬 Get in Touch")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Have a question or want to work together? Feel free to reach out!")
        st.markdown(f"📧 **Email:** [{profile['email']}](mailto:{profile['email']})")
        
        st.subheader("Send a Message")
        with st.form("contact_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            message = st.text_area("Message")
            submit = st.form_submit_button("Send Message")
            
            if submit:
                st.success("Thanks! I'll get back to you soon.")
    
    with col2:
        # Resume Download
        st.subheader("Resume")
        st.markdown("Interested in my professional background? Download my comprehensive resume.")
        
        # In a real app, read binary file
        # with open("assets/resume.pdf", "rb") as pdf:
        #    st.download_button(...)
        st.download_button(
            label="📄 Download Resume (PDF)",
            data="Fake Resume Content",
            file_name="resume.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>© 2025 {profile['name']}. Built with Streamlit & Python.</div>", unsafe_allow_html=True)