# Streamlit Portfolio Ideas

## Core Concept
A modern, interactive personal portfolio showcasing skills, projects, and professional background. The UI should be clean, responsive, and easy to navigate.

## Proposed Sections

### 1. Home / About Me ✅ (Consolidated)
- **Visuals**: A professional profile photo (circular or stylized card) + a banner or dynamic background.
- **Content**: 
    -   Name, Title, and Tagline.
    -   **Bio**: Key introduction.
    -   **Timeline**: Consolidated into the Home page for immediate visibility.
- **Call to Action**: (Simplified) Buttons removed for cleaner look, navigation via sidebar.
- **Socials**: Icons for GitHub and LinkedIn (Twitter removed).

### 2. [Section Removed] (Merged into Home)

### 3. Skills ✅ (Implemented)
- **Content**: Detailed breakdown of Core Skills including:
    - Cloud Data Platforms (AWS, Azure).
    - Data Engineering & Architecture.
    - DevOps & Observability.
- **Visualization**: Clean, categorized tags/badges (removed progress bars for a cleaner look).

### 4. Project Gallery (The Core) ✅ (Implemented)
- **Layout**: a Grid layout of "Project Cards".
- **Card Content**:
    - Project Thumbnail/Image.
    - Title & Short Description.
    - Technology tags (badges).
    - Links: "Source Code" (GitHub) and "Live Demo".
- **Filter**: A sidebar filter to select projects by category (e.g., "Machine Learning", "Web App", "Automation").

### 5. AI Flashcard Generator ✅ (Implemented)
**Requirements Met**:
1.  **Model Selection**: User can select available xAI models (e.g., grok-beta).
2.  **Content Generation**: 
    -   User inputs text notes.
    -   Model generates **3 flashcards**.
    -   **Cloud Ready**: Uses xAI (Grok) API for fast inference (requires API key).
3.  **Interaction**:
    -   Flashcards show the **Front** (Question) by default.
    -   Clicking on the card (or toggle button) toggles between **Front/Back**.

**Technical Implementation**:
-   Connects to **xAI API** (`/v1/chat/completions`).
-   Securely handles API keys via `st.secrets` (`GROK_API_KEY`) with robust nested-dict handling.
-   Uses `st.session_state` to persist cards.

## Design & Aesthetics
- **Theme**: Dark mode by default (sleek, developer-focused) or a clean Light mode.
- **Colors**: Pick a primary accent color (e.g., Teal, Indigo, or Orange) to use on buttons and headers.
- **Typography**: Custom fonts via CSS (e.g., 'Inter', 'Roboto') for a polished look.
- **Animations**: Subtle entry animations using custom CSS or `streamlit-lottie` for engaging illustrations.

## Technical Structure
- `main.py`: The entry point and navigation manager. **(Current Approach)**
- `assets/`: Folder for images and CSS.
- `data/`: JSON files (`profile.json`, `skills.json`, `projects.json`) store all content. ✅
- Future Refactoring: Move page logic to `views/` if `main.py` grows too large.
