# NBA Common Teammates Finder

This project automates the process of finding common teammates between a group of NBA players using data from [RealGM](https://basketball.realgm.com/nba/).

## Prerequisites

- **Python 3.x**
- **Google Chrome** installed.
- **Python Packages**:
  ```bash
  pip install playwright beautifulsoup4
  playwright install
  ```
- **Playwright**: Handles browser binaries automatically.

## Overview

The script `nba_common_teammates.py` performs the following steps:

1.  **Configuration**: Defines groups of players to analyze.
2.  **Scraping**: Uses **Playwright** (headed mode for stealth) to navigate to each player's URL. It employs implicit waits to ensure data loads dynamically.
3.  **Parsing**: Uses **BeautifulSoup** to parse the HTML and extract the list of teammates from the table.
4.  **Intersection**: Compares the lists of teammates for all specified players and finds the intersection (players who played with *everyone* in the group).
5.  **Output**: Prints the list of common teammates to the console.

## Usage

1.  Open `nba_common_teammates.py`.
2.  Modify the `TARGET_PLAYERS` list at the bottom to select which group of players to analyze.
    ```python
    # Example Configuration
    TARGET_PLAYERS = [
        'Giannis Antetokounmpo',
        'James Harden',
        'Nikola Jokic'
    ]
    ```
3.  Run the script:
    ```bash
    python nba_common_teammates.py
    ```

## Reference Links

- **NBA Home**: [RealGM NBA](https://basketball.realgm.com/nba/)
- **Player Lists (by Year)**: e.g., [2025-2026 Players](https://basketball.realgm.com/nba/players/2026)
- **Top 75 Players**: [NBA Top 75](https://basketball.realgm.com/nba/awards/top_75)
- **Awards**:
    - [MVPs](https://basketball.realgm.com/nba/awards/by-type/Most-Valuable-Player/1)
    - [Sixth Man of the Year](https://basketball.realgm.com/nba/awards/by-type/Sixth-Man-of-the-Year/3)
    - [Finals MVPs](https://basketball.realgm.com/nba/awards/by-type/NBA-Finals-MVP/17)

## Logic: Adding New Players

The script uses a dynamic search mechanism. Ensure the player names you use are unique enough to likely result in a direct match or a small list of results.

### Search Disambiguation Flow

1.  **Search**: The script searches for the player name on RealGM.
2.  **Redirect Check**:
    *   **Direct Match**: If the search automatically redirects to a player profile (URL format: `.../player/{Name}/Summary/{ID}`), the script proceeds with this player.
    *   **Multiple Results**: If no redirect occurs, the script checks for a "Players Found" results page.
3.  **Filtering (if multiple results)**:
    *   It parses the results table.
    *   It looks for players who have data in the **NBA Teams** column (ignoring empty entries or dashes). Get the URL from a href field.
4.  **Selection**:
    *   **Unique Valid Candidate**: If exactly *one* player remains after filtering, that player is selected.
    *   **Ambiguous/None**: If *multiple* valid players remain, or *none*, the script **aborts** for that player to avoid processing the wrong person.