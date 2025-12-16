from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_pass(message):
    print(f"{GREEN}{message}{RESET}")

def print_fail(message):
    print(f"{RED}{message}{RESET}")

def verify_movie(movie_data, expected_data, expected_stars):
    """
    Verifies actual movie data against expected data.
    Returns True if passed, False otherwise.
    """
    print(f"\n--- Verifying Test Case: Movie #{movie_data['Rank']} ({movie_data['Title']}) ---")
    
    passed = True
    
    # Check standard fields
    for key, val in expected_data.items():
        if movie_data.get(key) != val:
            print_fail(f"FAIL: {key} mismatch. Expected '{val}', Got '{movie_data.get(key)}'")
            passed = False
        else:
            print_pass(f"PASS: {key} matches '{val}'")
            
    # Check Stars specifically
    if movie_data.get('Stars') != expected_stars:
         print_fail(f"FAIL: Stars mismatch. Expected '{expected_stars}', Got '{movie_data.get('Stars')}'")
         passed = False
    else:
         print_pass(f"PASS: Stars match '{expected_stars}'")
         
    if passed:
        print_pass(">>> Test Case PASSED! <<<")
    else:
        print_fail(">>> Test Case FAILED! <<<")
        
    print("-------------------------------------------------")
    return passed

def main():
    print("Starting IMDB Top 250 Scraper (Fresh)...")
    
    url = 'https://www.imdb.com/chart/top/?ref_=vp_nv_menu&view=detailed'
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to {url}...")
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Wait for list to appear
            print("Waiting for movie list...")
            # Wait for list items to ensure content is there
            page.wait_for_selector('li.ipc-metadata-list-summary-item', state='visible', timeout=30000)
            
            # Scroll to load all items
            print("Scrolling to load all movies...")
            previous_count = 0
            while True:
                # Press End to scroll
                page.keyboard.press('End')
                time.sleep(1) # wait for load
                
                # Check count
                items = page.query_selector_all('li.ipc-metadata-list-summary-item')
                current_count = len(items)
                print(f"Loaded {current_count} movies...")
                
                if current_count >= 250:
                    break
                
                if current_count == previous_count:
                    # Retry scroll a few times if stuck? Or just break if it stabilizes
                    pass 
                previous_count = current_count
                
            items = page.query_selector_all('li.ipc-metadata-list-summary-item')
            print(f"Total movies found: {len(items)}")
            
            movies_data = []
            
            for index, item in enumerate(items):
                try:
                    # Rank
                    rank = "N/A"
                    rank_el = item.query_selector('div.ipc-signpost__text')
                    if rank_el:
                        rank_text = rank_el.inner_text().strip()
                        # expecting "#1", remove #
                        rank = rank_text.replace('#', '')
                    
                    # Title
                    title = "N/A"
                    title_el = item.query_selector('h3.ipc-title__text')
                    if title_el:
                        title = title_el.inner_text().strip()
                        if re.match(r'^\d+\.\s+', title):
                             title = re.sub(r'^\d+\.\s+', '', title)

                    # Metadata (Year, Duration, Classification)
                    year = "N/A"
                    duration = "N/A"
                    classification = "N/A"
                    
                    bg_metadata = item.query_selector_all('div.dli-title-metadata span.dli-title-metadata-item')
                    # Expecting order: Year, Duration, Classification
                    if len(bg_metadata) >= 1:
                        year = bg_metadata[0].inner_text().strip()
                    if len(bg_metadata) >= 2:
                        duration = bg_metadata[1].inner_text().strip()
                        if re.match(r'^\d+m$', duration):
                            duration = "0h " + duration
                    if len(bg_metadata) >= 3:
                        classification = bg_metadata[2].inner_text().strip()
                        
                    # Rating
                    rating = "N/A"
                    rating_el = item.query_selector('span.ipc-rating-star--rating')
                    if rating_el:
                        rating = rating_el.inner_text().strip()
                        
                    # Votes
                    votes = "N/A"
                    votes_el = item.query_selector('span.ipc-rating-star--voteCount')
                    if votes_el:
                        votes_text = votes_el.inner_text().strip()
                        votes = re.sub(r'[()\s]', '', votes_text)
                        
                    # Description
                    description = "N/A"
                    desc_el = item.query_selector('div.ipc-html-content-inner-div')
                    if desc_el:
                        description = desc_el.inner_text().strip()
                        
                    # Directors & Stars
                    directors = "N/A"
                    stars_list = []
                    
                    all_spans = item.query_selector_all('span')
                    
                    for i, sp in enumerate(all_spans):
                        txt = sp.inner_text().strip()
                        # Check for singular or plural "Director" / "Directors"
                        # Exact match or startswith? Usually text is exact "Director" or "Directors".
                        if txt in ["Director", "Directors"]:
                            parent = sp.query_selector('xpath=..')
                            if parent:
                                links = parent.query_selector_all('a.ipc-link')
                                dirs = [l.inner_text().strip() for l in links]
                                if dirs:
                                    directors = ", ".join(dirs)
                                    
                        if txt == "Stars":
                            parent = sp.query_selector('xpath=..')
                            if parent:
                                links = parent.query_selector_all('a.ipc-link')
                                strs = [l.inner_text().strip() for l in links]
                                if strs:
                                    stars_list = strs

                    stars = ", ".join(stars_list)

                    # Build Data Object
                    movie_data = {
                        'Rank': rank,
                        'Title': title,
                        'Year': year,
                        'Duration': duration,
                        'Classification': classification,
                        'Rating': rating,
                        'Votes': votes,
                        'Description': description,
                        'Directors': directors,
                        'Stars': stars
                    }
                    
                    # --- VERIFICATION LOGIC ---
                    
                    # Movie #182: Barry Lyndon
                    if rank == '182':
                        expected_182 = {
                            'Title': 'Barry Lyndon',
                            'Year': '1975',
                            'Duration': '3h 5m',
                            'Classification': 'PG',
                            'Rating': '8.1',
                            'Votes': '200K',
                            'Directors': 'Stanley Kubrick'
                        }
                        expected_stars_182 = "Ryan O'Neal, Marisa Berenson, Patrick Magee"
                        verify_movie(movie_data, expected_182, expected_stars_182)

                    # Movie #184: Million Dollar Baby
                    if rank == '184':
                        expected_184 = {
                            'Title': 'Million Dollar Baby',
                            'Year': '2004',
                            'Duration': '2h 12m',
                            'Classification': 'PG-13',
                            'Rating': '8.1',
                            'Votes': '758K',
                            'Directors': 'Clint Eastwood'
                        }
                        expected_stars_184 = "Hilary Swank, Clint Eastwood, Morgan Freeman"
                        verify_movie(movie_data, expected_184, expected_stars_184)
                        
                    # Movie #209: The General
                    if rank == '209':
                        expected_209 = {
                            'Title': 'The General',
                            'Year': '1926',
                            'Duration': '1h 18m',
                            'Classification': 'Passed',
                            'Rating': '8.1',
                            'Votes': '105K',
                            'Directors': 'Clyde Bruckman, Buster Keaton'
                        }
                        expected_stars_209 = "Buster Keaton, Marion Mack, Glen Cavender"
                        verify_movie(movie_data, expected_209, expected_stars_209)
                    
                    movies_data.append(movie_data)
                    
                except Exception as e:
                    print_fail(f"Error extracting item {index}: {e}")

            # Save
            df = pd.DataFrame(movies_data)
            df.to_csv('Top_250_Movies.csv', index=False)
            print("Saved Top_250_Movies.csv")
            
        except Exception as e:
            print_fail(f"Global Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
