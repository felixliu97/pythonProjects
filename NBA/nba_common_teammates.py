import re
import time
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Global Timeouts (ms)
TIMEOUT_NAVIGATION = 30000
TIMEOUT_SELECTOR = 15000
TIMEOUT_SHORT = 3000

class NBATeammatesScraper:
    def __init__(self, headless=True, log_prefix=""):
        self.headless = headless
        self.log_prefix = log_prefix
        self.browser = None
        self.context = None
        self.playwright = None

    def _log(self, message):
        print(f"{self.log_prefix}{message}")

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self._log("Launching Browser...")
        # Add stealth arguments
        args = [
            '--disable-blink-features=AutomationControlled',
            '--start-maximized',
        ]
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=args
        )
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        # Inject stealth script to hide webdriver property
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def find_player_teammates_url(self, page, player_name):
        """
        Searches for a player and returns their Teammates page URL.
        """
        # User Request: Replace - with space
        clean_name = player_name.replace('-', ' ')
        self._log(f"Searching for player: {player_name} (Query: {clean_name})")
        
        # RealGM uses + for spaces
        encoded_name = urllib.parse.quote_plus(clean_name)
        search_url = f"https://basketball.realgm.com/search?q={encoded_name}"
        
        try:
            self._log(f"  Navigating to search: {search_url}")
            try:
                # 'commit' is faster; we rely on selectors later
                page.goto(search_url, timeout=TIMEOUT_NAVIGATION, wait_until='commit')
            except Exception as e:
                self._log(f"  Navigation check: {e}")
                # Continue if we are on a valid page despite timeout
            
            # Debug: where are we?
            self._log(f"  Current URL: {page.url}")
            
            # 1. Check if we landed directly on a profile (RealGM does this for exact matches)
            try:
                # Wait briefly for either teammates link OR search results
                teammates_link = page.wait_for_selector('a[href*="/Teammates/"]', timeout=TIMEOUT_SHORT)
                if teammates_link:
                    self._log(f"  Found 'Teammates' link directly.")
                    href = teammates_link.get_attribute('href')
                    if href.startswith('http'):
                        return href
                    return f"https://basketball.realgm.com{href}"
            except Exception:
                pass # Not found immediately

            # 2. Check for search results
            self._log("  Checking for search results list...")
            try:
                # Wait for search results container - specificity based on user snippet
                # <table data-toggle="table" ...>
                results_table = page.wait_for_selector('table[data-toggle="table"] tbody', timeout=TIMEOUT_SELECTOR)
                
                if results_table:
                    self._log("  Found search results table. Analyzing...")
                    # We need to re-query elements to ensure we have fresh handles
                    rows = results_table.query_selector_all('tr')
                    candidates = []
                    
                    for row in rows:
                        cols = row.query_selector_all('td')
                        if not cols: 
                            continue
                        
                        # Screenshot shows: Player (1st), ..., NBA (Last)
                        # 1st Column: <td class="nowrap"><a href="...">Name</a></td>
                        name_col = cols[0]
                        nba_col = cols[-1]
                        
                        nba_text = nba_col.inner_text().strip()
                        
                        # Filter: NBA column must have value (teams) vs empty/dash
                        if nba_text and len(nba_text) > 1:
                            name_link = name_col.query_selector('a')
                            if name_link:
                                candidates.append({
                                    'name': name_link.inner_text(),
                                    'href': name_link.get_attribute('href'),
                                    'nba_teams': nba_text,
                                    'element': name_link # Keep element if we want to click, or just goto href
                                })
                    
                    self._log(f"  Found {len(candidates)} candidates with NBA teams.")
                    
                    if len(candidates) == 1:
                        # Exact match logic
                        c = candidates[0]
                        self._log(f"  Selecting unique candidate: {c['name']} ({c['nba_teams'][:20]}...)")
                        
                        # Doc requirement: "Get the URL from a href field"
                        # "it should be in the same format as https://basketball.realgm.com/player/{Player_Name}/Summary/{Player_ID}"
                        target_href = c['href']
                        self._log(f"  Target Href: {target_href}")
                        
                        # Navigate directly using the href found
                        target_href = c['href']
                        if target_href.startswith('http'):
                            full_profile_url = target_href
                        else:
                            full_profile_url = f"https://basketball.realgm.com{target_href}"
                            
                        self._log(f"  Navigating to profile: {full_profile_url}")
                        page.goto(full_profile_url, timeout=TIMEOUT_NAVIGATION, wait_until='commit')
                        
                        # Now find Teammates link
                        teammates_link = page.wait_for_selector('a[href*="/Teammates/"]', timeout=TIMEOUT_SELECTOR)
                        if teammates_link:
                            href = teammates_link.get_attribute('href')
                            if href.startswith('http'):
                                return href
                            return f"https://basketball.realgm.com{href}"
                            
                    elif len(candidates) > 1:
                        self._log(f"  ABORT: Ambiguous results. {len(candidates)} players have NBA teams: {[c['name'] for c in candidates]}")
                        return None
                    else:
                        self._log("  No valid candidates found (no NBA teams listed in search results).")
                        return None

            except Exception as e:
                self._log(f"  Error analyzing search results: {e}")
                
            self._log(f"  Could not find Teammates link or Valid Search Result for {player_name}")
            page.screenshot(path=f"debug_fail_{encoded_name}.png")
            return None

        except Exception as e:
            self._log(f"  Error finding URL for {player_name}: {e}")
            return None

    def get_teammates_list(self, page, teammates_url):
        self._log(f"  Scraping teammates from: {teammates_url}")
        try:
            page.goto(teammates_url, timeout=TIMEOUT_NAVIGATION, wait_until='domcontentloaded')
            
            # Wait for table
            page.wait_for_selector('tbody', timeout=TIMEOUT_SELECTOR)
            
            # Extract names
            # Using BeautifulSoup for parsing as it's often robust
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            teammates = []
            table = soup.find('tbody')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if cols:
                        # First column usually has the name link
                        link = cols[0].find('a')
                        if link:
                            teammates.append(link.get_text().strip())
            
            self._log(f"  Found {len(teammates)} teammates.")
            return teammates
            
        except Exception as e:
            self._log(f"  Error scraping teammates: {e}")
            return []

    def get_recent_winners(self, page, award_url, n=3):
        """
        Scrapes the last n unique winners from an award page.
        """
        self._log(f"  Fetching last {n} unique winners from: {award_url}")
        winners = []
        try:
            page.goto(award_url, timeout=TIMEOUT_NAVIGATION, wait_until='domcontentloaded')
            page.wait_for_selector('table tbody', timeout=TIMEOUT_SELECTOR)
            
            # RealGM award tables usually have Player in the 2nd column (index 1) for yearly awards
            # Columns: Season | Player | Team ...
            rows = page.query_selector_all('table tbody tr')
            
            for row in rows:
                cols = row.query_selector_all('td')
                if len(cols) > 1:
                    # Player name usually in 2nd column
                    player_name_el = cols[1].query_selector('a')
                    if player_name_el:
                        name = player_name_el.inner_text().strip()
                        if name not in winners:
                            winners.append(name)
                        
                        if len(winners) >= n:
                            break
                            
            self._log(f"  Found winners: {winners}")
            return winners

        except Exception as e:
            self._log(f"  Error fetching winners: {e}")
            return []

import concurrent.futures

# Global Cache for Teammates
# Format: {'Player Name': set(['Teammate1', 'Teammate2', ...])}
TEAMMATES_CACHE = {}

def fetch_player_teammates_safe(player_name):
    """
    Thread-safe wrapper to fetch teammates for a single player.
    Creates its own Playwright instance to avoid context conflicts.
    """
    # 1. Check Cache
    if player_name in TEAMMATES_CACHE:
        print(f"  [CACHE HIT] {player_name}")
        return TEAMMATES_CACHE[player_name]

    print(f"  [FETCHING] {player_name}...")
    teammates_set = set()
    
    try:
        with NBATeammatesScraper(headless=True, log_prefix=f"[{player_name}] ") as scraper:
            page = scraper.context.new_page()
            url = scraper.find_player_teammates_url(page, player_name)
            
            if url:
                teammates = scraper.get_teammates_list(page, url)
                teammates_set = set(teammates)
            else:
                print(f"[{player_name}]   [WARN] Could not find URL for {player_name}")
                
    except Exception as e:
        print(f"[{player_name}]   [ERROR] {player_name}: {e}")

    # Update Cache (even if empty to avoid refetching failed players repeatedly)
    TEAMMATES_CACHE[player_name] = teammates_set
    return teammates_set

def find_common_teammates(players_list):
    if not players_list:
        return []

    player_teammate_sets = []
    
    # Standard ThreadPoolExecutor for parallel network requests
    # Limit max_workers to avoid resource exhaustion/rate limiting
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Map returns results in the order of input iterable
        results = list(executor.map(fetch_player_teammates_safe, players_list))
        player_teammate_sets = results

    # Compute Intersection
    if not player_teammate_sets:
        return []
        
    # Start with the first player's teammates
    common = player_teammate_sets[0]
    
    # Intersect with the rest
    for t_set in player_teammate_sets[1:]:
        common = common.intersection(t_set)
        
        # Optimization: Early exit if intersection becomes empty
        if not common:
            print("  Intersection is empty. No straight matches.")
            break
            
    return list(common)

# ANSI Colors
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

# --- Main Execution ---

if __name__ == "__main__":
    # Define awards to test
    AWARDS_CONFIG = {
        "Last 3 MVPs": "https://basketball.realgm.com/nba/awards/by-type/Most-Valuable-Player/1",
        "Last 3 Sixth Man of the Year": "https://basketball.realgm.com/nba/awards/by-type/Sixth-Man-of-the-Year/3",
        "Last 3 Finals MVPs": "https://basketball.realgm.com/nba/awards/by-type/NBA-Finals-MVP/17"
    }

    # We need to fetch players first, then find teammates. 
    # To avoid nested Playwright instances (which causes errors), we separate the contexts.
    
    for group_name, url in AWARDS_CONFIG.items():
        print(f"\n{'='*60}")
        print(f"Processing {group_name}")
        print(f"{'='*60}")
        
        players = []
        # 1. Get Players Dynamically
        with NBATeammatesScraper(headless=True) as scraper:
            page = scraper.context.new_page()
            players = scraper.get_recent_winners(page, url, n=3)
        
        if not players:
            print("Failed to fetch players. Skipping.")
            continue
            
        print(f"Target Players: {players}")
        
        # 2. Find Common Teammates
        # This function creates its own fresh Scraper instance, so we do it AFTER the previous one closes.
        print(f"Finding common teammates for: {players}")
        result = find_common_teammates(players)
        
        if result:
            print(f"\n{GREEN}Common Teammate(s) ({len(result)}):")
            for p in sorted(result):
                print(f"- {p}")
            print(RESET)
        else:
            print(f"\n{BLUE}No common teammates found!{RESET}")
        
        time.sleep(3)
