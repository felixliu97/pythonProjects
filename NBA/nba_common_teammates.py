import re
import time
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class NBATeammatesScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        print("Launching Browser...")
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
        print(f"Searching for player: {player_name}")
        # RealGM uses + for spaces
        encoded_name = urllib.parse.quote_plus(player_name)
        search_url = f"https://basketball.realgm.com/search?q={encoded_name}"
        
        try:
            print(f"  Navigating to search: {search_url}")
            try:
                # 'commit' is faster; we rely on selectors later
                page.goto(search_url, timeout=30000, wait_until='commit')
            except Exception as e:
                print(f"  Navigation check: {e}")
                # Continue if we are on a valid page despite timeout
            
            # Debug: where are we?
            print(f"  Current URL: {page.url}")
            
            # 1. Check if we landed directly on a profile (RealGM does this for exact matches)
            try:
                # Wait briefly for either teammates link OR search results
                teammates_link = page.wait_for_selector('a[href*="/Teammates/"]', timeout=15000)
                if teammates_link:
                    print(f"  Found 'Teammates' link directly.")
                    href = teammates_link.get_attribute('href')
                    full_url = f"https://basketball.realgm.com{href}"
                    return full_url
            except Exception:
                pass # Not found immediately

            # 2. Check for search results
            print("  Checking for search results list...")
            try:
                # Wait for search results container - specificity based on user snippet
                # <table data-toggle="table" ...>
                results_table = page.wait_for_selector('table[data-toggle="table"] tbody', timeout=15000)
                
                if results_table:
                    print("  Found search results table. Analyzing...")
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
                    
                    print(f"  Found {len(candidates)} candidates with NBA teams.")
                    
                    if len(candidates) == 1:
                        # Exact match logic
                        c = candidates[0]
                        print(f"  Selecting unique candidate: {c['name']} ({c['nba_teams'][:20]}...)")
                        
                        # Doc requirement: "Get the URL from a href field"
                        # "it should be in the same format as https://basketball.realgm.com/player/{Player_Name}/Summary/{Player_ID}"
                        target_href = c['href']
                        print(f"  Target Href: {target_href}")
                        
                        # Navigate directly using the href found
                        full_profile_url = f"https://basketball.realgm.com{target_href}"
                        print(f"  Navigating to profile: {full_profile_url}")
                        page.goto(full_profile_url, timeout=30000, wait_until='commit')
                        
                        # Now find Teammates link
                        teammates_link = page.wait_for_selector('a[href*="/Teammates/"]', timeout=15000)
                        if teammates_link:
                            href = teammates_link.get_attribute('href')
                            return f"https://basketball.realgm.com{href}"
                            
                    elif len(candidates) > 1:
                        print(f"  ABORT: Ambiguous results. {len(candidates)} players have NBA teams: {[c['name'] for c in candidates]}")
                        return None
                    else:
                        print("  No valid candidates found (no NBA teams listed in search results).")
                        return None

            except Exception as e:
                print(f"  Error analyzing search results: {e}")
                
            print(f"  Could not find Teammates link or Valid Search Result for {player_name}")
            page.screenshot(path=f"debug_fail_{encoded_name}.png")
            return None

        except Exception as e:
            print(f"  Error finding URL for {player_name}: {e}")
            return None

    def get_teammates_list(self, page, teammates_url):
        print(f"  Scraping teammates from: {teammates_url}")
        try:
            page.goto(teammates_url, timeout=30000, wait_until='domcontentloaded')
            
            # Wait for table
            page.wait_for_selector('tbody', timeout=10000)
            
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
            
            print(f"  Found {len(teammates)} teammates.")
            return teammates
            
        except Exception as e:
            print(f"  Error scraping teammates: {e}")
            return []

def find_common_teammates(players_list):
    common = []
    first = True
    
    with NBATeammatesScraper(headless=False) as scraper:
        page = scraper.context.new_page()
        
        for player_name in players_list:
            # 1. Find URL
            url = scraper.find_player_teammates_url(page, player_name)
            if not url:
                print(f"Skipping {player_name} (URL not found)")
                # If we can't find one player, intersection might be invalid or empty? 
                # Strict intersection means if one is missing, result is likely empty or we abort.
                # Let's treat it as empty set.
                if first:
                    common = []
                    first = False
                else:
                    common = []
                break # Stop processing
            
            # 2. Scrape Teammates
            teammates = scraper.get_teammates_list(page, url)
            
            # 3. Intersect
            if first:
                common = teammates
                first = False
            else:
                common = list(set(common).intersection(teammates))
            
            # Optimization: If common is empty, no need to continue
            if not common:
                print("  Intersection is empty. No straight matches.")
                break
                
            # Nice delay to avoid rate limiting
            time.sleep(2)

    return common

# --- Main Execution ---

TARGET_PLAYERS = [
    'Giannis Antetokounmpo',
    'James Harden',
    'Nikola Jokic'
]

if __name__ == "__main__":
    print(f"Finding common teammates for: {TARGET_PLAYERS}")
    
    result = find_common_teammates(TARGET_PLAYERS)
    
    if result:
        print(f"\nCommon Teammate(s) ({len(result)}):")
        for p in sorted(result):
            print(f"- {p}")
    else:
        print("\nNo common teammates found!")
