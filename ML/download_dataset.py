import os
import requests
import random
import string
import concurrent.futures

# Configuration
TARGET_DIR = r"e:\repos\pythonProjects\ML\Cats_Dogs"
CATS_COUNT = 50
DOGS_COUNT = 50
MAX_WORKERS = 10

# APIs
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"
DOG_API_URL = "https://api.thedogapi.com/v1/images/search"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_random_string(length=10):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def download_image(args):
    url, prefix, directory = args
    filename = f"{prefix}-{get_random_string()}.jpg"
    filepath = os.path.join(directory, filename)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        # print(f"Downloaded {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def fetch_urls(api_url, count):
    urls = []
    # Fetch in batches
    params = {
        'limit': count,
        'mime_types': 'jpg,png', # No gifs
        'size': 'med' 
    }
    
    # API Max limit per request is usually 10-25 free. Loop until we have enough.
    while len(urls) < count:
        needed = count - len(urls)
        fetch_limit = min(needed, 50) # Request up to 50
        params['limit'] = fetch_limit
        
        try:
            resp = requests.get(api_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            new_urls = [item['url'] for item in data]
            urls.extend(new_urls)
            
            if not new_urls:
                print("Warning: API returned no images. Retrying...")
                
        except Exception as e:
            print(f"API Fetch Error: {e}")
            break
            
    return urls[:count]

def main():
    ensure_dir(TARGET_DIR)
    print("Clearing old images (handled by user command usually, but safe to just write new files)...")
    
    print("Fetching Cat URLs...")
    cat_urls = fetch_urls(CAT_API_URL, CATS_COUNT)
    
    print("Fetching Dog URLs...")
    dog_urls = fetch_urls(DOG_API_URL, DOGS_COUNT)
    
    tasks = []
    tasks.extend([(url, "cat", TARGET_DIR) for url in cat_urls])
    tasks.extend([(url, "dog", TARGET_DIR) for url in dog_urls])
    
    print(f"Downloading {len(tasks)} images with {MAX_WORKERS} threads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(download_image, tasks))
        
    print(f"Done. Successfully downloaded {sum(results)} images.")

if __name__ == "__main__":
    main()
