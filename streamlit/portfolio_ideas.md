# Streamlit Portfolio Ideas

## Core Concept
A modern, interactive personal portfolio showcasing skills, projects, and professional background. The UI should be clean, responsive, and easy to navigate.

## Proposed Sections

### Home / About Me ✅ (Consolidated)
- **Visuals**: A professional profile photo (circular or stylized card) + a banner or dynamic background.
- **Content**: 
    -   Name, Title, and Tagline.
    -   **Bio**: Key introduction.
    -   **Timeline**: Consolidated into the Home page for immediate visibility.
- **Call to Action**: (Simplified) Buttons removed for cleaner look, navigation via sidebar.
- **Socials**: Icons for GitHub and LinkedIn (Twitter removed).

### Skills ✅ (Implemented)
- **Content**: Detailed breakdown of Core Skills including:
    - Artificial Intelligence & LLMs (GenAI, RAG, Bedrock).
    - Cloud Data Platforms (AWS, Azure).
    - Data Engineering & Architecture.
    - DevOps & Observability.
- **Visualization**: Clean, categorized tags/badges.

### Project Gallery (The Core) ✅ (Implemented)
- **Layout**: a Grid layout of "Project Cards".
- **Card Content**:
    - Project Thumbnail/Image (Supports local and remote images).
    - Title & Short Description.
    - Technology tags (badges).
    - Links: "Try it Live" (Green Primary Button) for interactive demos, "Live Demo" for external links.
- **Interactive Projects**: Cards open detailed tools within the gallery using `st.session_state`.
- **Filter**: A sidebar filter to select projects by category.

### AI Flashcard Generator ✅ (Integrated into Projects)
**Status**: Implemented as an interactive sub-project within the Project Gallery.

**Features**:
1.  **AI Powered**: Uses **Gemini 2.5 Flash** for high-speed generation.
2.  **Content Generation**: 
    -   User inputs study notes.
    -   AI generates 3 structured flashcards (Question/Answer).
3.  **Interaction**:
    -   Interactive "Flip" animation (state-based).
    -   Integrated locally; no redirect needed.

**Technical Implementation**:
-   **API**: Google Gemini API (`generativelanguage.googleapis.com`).
-   **Security**: API keys via `st.secrets` (`GEMINI_API_KEY`).
-   **State Management**: Uses `active_project` state to swap views dynamically.
-   **Location**: `projects/flashcards.py` (Refactored to standalone module).

### ASX Stock Monitor ✅ (Integrated into Projects)
**Status**: Implemented as an interactive sub-project within the Project Gallery.

**Features**:
1.  **Live Market Data**: Tracks **100+ ASX Blue-Chip Stocks** (expanded from 50).
2.  **Technical Analysis**:
    -   Calculates RSI (14-day), Momentum, and Volatility windows.
    -   Custom "Score" algorithm ranking stocks by safety & growth potential.
3.  **Visualization (Enhanced UI)**:
    -   **Sortable Table**: JavaScript-powered headers for instant sorting (Click to sort).
    -   **Styling**: Custom CSS for alternate row shading (zebra stripes), sticky headers, and distinct hover effects.
    -   **Key Metrics**: Metrics dashboard highlighting Top Safe Stock, Top Gainer, and Highest Momentum.
    -   **RSI Alerts**: Visual pills causing alert for Overbought/Oversold conditions.

**Technical Implementation**:
-   **Data Source**: `yfinance` API (real-time data).
-   **Architecture**: Uses `ThreadPoolExecutor` for concurrent data fetching (10x threads).
-   **Package Structure**: Logic encapsulated in `projects/asx_monitor.py`.
-   **Performance**: Caches data (`st.cache_data`) for 1 hour.

## Design & Aesthetics
- **Theme**: Dark mode by default (sleek, developer-focused) or a clean Light mode.
- **Colors**: 
    -   Header Accent: Deep Blue (`#0066cc`).
    -   Primary Action Buttons: Vibrant Green (`#28a745`) for "Try it Live" and key actions.
- **Typography**: Custom 'Inter' font via Google Fonts for a polished look.
- **Tables**: Custom HTML/CSS rendering for precise control over styling and interactivity (replacing standard `st.dataframe`).

## Technical Structure
- `main.py`: The entry point and navigation manager. **(Lightweight)**
- `projects/`: Dedicated package for sub-project modules.
    - `asx_monitor.py`: Financial data fetching and processing logic. ✅
    - `flashcards.py`: AI Flashcard Generator logic & UI. ✅
- `images/`: Stores project thumbnails (e.g., `AI_Stock_Monitor.png`).
- `data/`: JSON files (`profile.json`, `skills.json`, `projects.json`) store content. ✅