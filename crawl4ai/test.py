import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_news_teasers():
    schema = {
        "name": "News Teaser Extractor",
        "baseSelector": ".wide-tease-item__wrapper",
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
                "type": "nested",
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

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        news_teasers = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(news_teasers)} news teasers")
        print(json.dumps(news_teasers[0], indent=2))

if __name__ == "__main__":
    asyncio.run(extract_news_teasers())