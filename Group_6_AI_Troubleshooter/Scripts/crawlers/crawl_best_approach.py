import asyncio
import csv
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=3, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://in.mathworks.com/help/slrealtime/ug/troubleshooting-basics.html", config=config)
        # data=json.loads(results.extracted_content)
        print(f"Crawled {len(results)} pages in total")
        with open("crawl_results_for_depth_3.csv", mode="w", newline="", encoding="utf-8") as file:
          writer = csv.writer(file)
          writer.writerow(["URL", "Extracted_Content","metadata"])  # Header

          for result in results:
              url = result.url
              # html = result.html if result.html else ""
              if result.extracted_content=="``` Internal Server Error ```":
                  extracted = ""
              elif result.extracted_content:
                  extracted = result.extracted_content
              else: 
                  extracted = ""
              metadata = result.metadata if result.metadata else ""
              writer.writerow([url, extracted, metadata])

if __name__ == "__main__":
    asyncio.run(main())