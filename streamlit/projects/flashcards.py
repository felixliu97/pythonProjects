import streamlit as st
import requests
import json
import os

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

def render_flashcard_generator():
    """Renders the AI Flashcard Generator UI"""
    if st.button("← Back to Gallery"):
        st.session_state.active_project = None
        st.rerun()

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
                
                # Container for the card
                card_container = st.container()
                
                # Determine what to show based on flip state
                if st.session_state[card_key]:
                    # Showing Back (Answer)
                    with card_container:
                        st.info(f"**Answer:**\n\n{card['back']}")
                        if st.button("Show Question", key=f"btn_{i}"):
                            st.session_state[card_key] = False
                            st.rerun()
                else:
                    # Showing Front (Question)
                    with card_container:
                        st.warning(f"**Question:**\n\n{card['front']}")
                        if st.button("Show Answer", key=f"btn_{i}"):
                            st.session_state[card_key] = True
                            st.rerun()
