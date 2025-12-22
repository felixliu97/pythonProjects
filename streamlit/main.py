import streamlit as st
import pandas as pd
import json
import os
import requests

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

# --- AI Flashcards Function ---
def generate_flashcards(notes, model, api_key):
    system_prompt = """You are an AI that generates flash cards from study notes. When provided with *Study Notes*, you will produce an array of objects where each object represents a flash card. Each flash card object must have a "front" property containing the question and a "back" property containing the answer. The output should be an array with three flash card objects. Do not include anything else other than the array of flash cards. Your response should ONLY contain the array of objects in the following format:
    [
        {"front": "question here", "back": "answer here"},
        {"front": "question here", "back": "answer here"},
        {"front": "question here", "back": "answer here"}
    ]
    """
    
    try:
        # Google Gemini API Endpoint
        # Using v1beta for now as it supports the features we need
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Proper Gemini API payload structure
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nCreate 3 flashcards from these notes:\n\n{notes}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(
            api_url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract content from Gemini response
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Robust JSON extraction
            try:
                # Gemini explicitly supports JSON mode, so it should return valid JSON
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback extraction if JSON mode fails or adds extra text
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx : end_idx + 1]
                    return json.loads(json_str)
                else:
                    st.error(f"Parsing Failed. The model returned:\n\n{content}")
                    print(f"DEBUG: Failed content: {content}") # Add debug print
                    return []
        else:
            st.error(f"Unexpected API response format: {result}")
            return []
            
    except requests.exceptions.HTTPError as e:
        # Improved error handling to show API details
        try:
            error_details = e.response.json()
            st.error(f"API Error ({e.response.status_code}): {json.dumps(error_details, indent=2)}")
        except:
            st.error(f"HTTP Error: {str(e)}\nResponse: {e.response.text}")
        return []
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        return []



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
st.sidebar.image("https://media.licdn.com/dms/image/v2/D5603AQGI3jtiRX8m1g/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1688468011137?e=1767830400&v=beta&t=hTjzT3Eafl9RM14u-YZdVLURNiqIdGzM_wwstIiPpYo", width=150)
st.sidebar.title(profile["name"])
st.sidebar.caption(profile["title"])

st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")

if "page" not in st.session_state:
    st.session_state.page = "Home"

def set_page(page_name):
    st.session_state.page = page_name

st.sidebar.button("🏠 Home", on_click=set_page, args=("Home",), use_container_width=True)
st.sidebar.button("🛠️ Skills", on_click=set_page, args=("Skills",), use_container_width=True)
st.sidebar.button("🚀 Projects", on_click=set_page, args=("Projects",), use_container_width=True)
st.sidebar.button("🧠 AI Flashcards", on_click=set_page, args=("AI Flashcards",), use_container_width=True)

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

elif page == "AI Flashcards":
    st.title("🧠 AI Flashcard Generator")
    st.markdown("Enter your study notes below and let AI generate flashcards for you.")
    
    # API Key Handling
    if "GEMINI_API_KEY" in st.secrets:
        raw_key = st.secrets["GEMINI_API_KEY"]
        if isinstance(raw_key, dict) and "value" in raw_key:
            api_key = raw_key["value"]
        else:
            api_key = raw_key
    else:
        st.error("Please add `GEMINI_API_KEY` to your `.streamlit/secrets.toml` file.")
        st.stop()

    # Model Selection
    selected_model = "gemini-2.5-flash"

    notes = st.text_area("Study Notes", height=200, placeholder="Paste your notes here...")
    
    generate_btn = st.button("Generate Flashcards", type="primary")

    if generate_btn:
        if not api_key:
            st.error("Please provide an API Key.")
        elif not notes:
            st.warning("Please enter some study notes.")
        else:
            with st.spinner(f"Generating flashcards using {selected_model}..."):
                generated_cards = generate_flashcards(notes, model=selected_model, api_key=api_key)
                if generated_cards:
                    st.session_state.flashcards = generated_cards
                    # Reset flip states for new cards
                    for i in range(len(generated_cards)):
                        st.session_state[f"flip_state_{i}"] = False
                    st.success("Flashcards generated!")
                else:
                    st.error("Failed to generate flashcards.")
                    
    # Display Flashcards from Session State
    if "flashcards" in st.session_state and st.session_state.flashcards:
        st.divider()
        st.subheader("Your Flashcards")
        
        # Grid Layout for Flashcards
        cols = st.columns(len(st.session_state.flashcards))
        
        for i, (col, card) in enumerate(zip(cols, st.session_state.flashcards)):
            with col:
                card_key = f"flip_state_{i}"
                if card_key not in st.session_state:
                    st.session_state[card_key] = False
                    
                is_flipped = st.session_state[card_key]
                
                # Styling based on state
                if is_flipped:
                    card_content = card['back']
                    card_label = "ANSWER"
                    bg_color = "#d4edda" # Light green
                    border_color = "#c3e6cb"
                    text_color = "#155724"
                    btn_text = "🔄 Flip back"
                else:
                    card_content = card['front']
                    card_label = "QUESTION"
                    bg_color = "#cce5ff" # Light blue
                    border_color = "#b8daff"
                    text_color = "#004085"
                    btn_text = "👀 Reveal"

                # Custom CSS Card (Fixed height for alignment)
                st.markdown(f"""
                <div style="
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 10px;
                    color: {text_color};
                    min-height: 200px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    box_shadow: 0 4px 6px rgba(0,0,0,0.05);
                ">
                    <div style="font-size: 1.2em; font-weight: 500;">{card_content}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button to toggle state
                def toggle_state(k=card_key):
                    st.session_state[k] = not st.session_state[k]
                    
                st.button(btn_text, key=f"btn_flip_{i}", on_click=toggle_state, use_container_width=True)
        else:
            if not st.session_state.flashcards:
                st.warning("Please enter some notes first.")

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>© 2025 {profile['name']}. Built with Streamlit & Python.</div>", unsafe_allow_html=True)