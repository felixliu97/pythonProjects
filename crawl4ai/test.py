import asyncio
import json
import sys

# Check for Python version compatibility at the start
if sys.version_info < (3, 10):
    print(f"Error: This script requires Python 3.10 or higher. You are using {sys.version}")
    print("The 'crawl4ai' library uses modern Python features (like union types X | Y) not available in older versions.")
    sys.exit(1)

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
except ImportError as e:
    print(f"Error importing crawl4ai: {e}")
    print("Please ensure crawl4ai is installed: pip install crawl4ai")
    sys.exit(1)
except TypeError as e:
    print(f"Error importing crawl4ai: {e}")
    print("This is likely due to running on an older Python version. Please upgrade to Python 3.10+.")
    sys.exit(1)

async def extract_news_teasers():
    """
    Asynchronously extracts news teasers from NBC News Business page using crawl4ai.
    
    This function defines a structured extraction schema and runs a crawler to fetch
    and parse the content based on CSS selectors.
    """
    
    # Define the extraction schema using a dictionary.
    # This schema tells the crawler exactly what fields to look for and how to find them using CSS selectors.
    schema = {
        "name": "News Teaser Extractor",
        "baseSelector": ".wide-tease-item__wrapper",  # The container for each news item
        "fields": [
            {
                "name": "category",
                "selector": ".unibrow span[data-testid='unibrow-text']",
                "type": "text",
            },
            {
                "name": "headline",
                "selector": ".wide-tease-item__headline",
                "type": "text",
            },
            {
                "name": "summary",
                "selector": ".wide-tease-item__description",
                "type": "text",
            },
            {
                "name": "time",
                "selector": "[data-testid='wide-tease-date']",
                "type": "text",
            },
            {
                "name": "image",
                "type": "nested",  # Nested type for extracting attributes from the image tag
                "selector": "picture.teasePicture img",
                "fields": [
                    {"name": "src", "type": "attribute", "attribute": "src"},
                    {"name": "alt", "type": "attribute", "attribute": "alt"},
                ],
            },
            {
                "name": "link",
                "selector": "a[href]",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }

    # Initialize the extraction strategy with the defined schema.
    # verbose=True enables detailed logging of the extraction process.
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # Use AsyncWebCrawler as a context manager to ensure proper resource cleanup.
    # verbose=True enables detailed logging of the crawling process.
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler on the specified URL.
        # bypass_cache=True ensures we fetch fresh content from the web.
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        # Verify that the crawl was successful
        if not result.success:
            print("Failed to crawl the page.")
            return

        # Parse the extracted JSON content
        news_teasers = json.loads(result.extracted_content)
        
        print(f"Successfully extracted {len(news_teasers)} news teasers")
        
        # Print the first item to verify the structure
        if news_teasers:
            print("Example extracted item:")
            print(json.dumps(news_teasers[0], indent=2))
        else:
            print("No items extracted.")

if __name__ == "__main__":
    # Run the asynchronous main function
    asyncio.run(extract_news_teasers())