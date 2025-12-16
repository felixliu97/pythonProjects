# IMDB Scraping Instructions

1. **Analyze Page Structure**
   Open [IMDB Top 250 Detailed View](https://www.imdb.com/chart/top/?ref_=vp_nv_menu&view=detailed), read its HTML, and understand the element structure.

2. **Scrape Data**
   Use Playwright to scrape the data from the page.

3. **Verify Data Extraction**
   Ensure you capture the correct values for:
   - Rank
   - Title
   - Year
   - Duration
   - Classification
   - Rating
   - Votes
   - Description
   - Director
   - Stars

   **Test Case (Movie #182):**
   ```yaml
   Rank: 182
   Title: Barry Lyndon
   Year: 1975
   Duration: 3h 5m
   Classification: PG
   Rating: 8.1
   Votes: 200K
   Description: An Irish rogue wins the heart of a rich widow and assumes her dead husband's aristocratic position in 18th-century England.
   Director: Stanley Kubrick
   Stars: Ryan O'Neal, Marisa Berenson, Patrick Magee
   ```

   **Test Case (Movie #184):**
   ```yaml
   Rank: 184
   Title: Million Dollar Baby
   Year: 2004
   Duration: 2h 12m
   Classification: PG-13
   Rating: 8.1
   Votes: 758K
   Description: Frankie, an ill-tempered old coach, reluctantly agrees to train aspiring boxer Maggie. Impressed with her determination and talent, he helps her become the best and the two soon form a close bond.
   Director: Clint Eastwood
   Stars: Hilary Swank, Clint Eastwood, Morgan Freeman
   ```

4. **Save Data**
   Save the extracted data to a CSV file.