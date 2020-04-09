from search_engines.utils import encode_url_str, extract_first, join_all, get_logger, http_search
from lxml.html import fromstring
from pathlib import Path
from aiohttp.client import ClientSession
from aiohttp.client_reqrep import ClientResponse
from typing import Dict, Tuple, List
import random
import asyncio

log_save_path = Path(__file__).parent.joinpath('logs/yahoo_search.log')
logger = get_logger("Yahoo Search", log_save_path)

async def parse_page(resp: ClientResponse, query: str) -> Tuple[List[Dict[str,str]],str]:
    html = await resp.text()
    root = fromstring(html)
    page_num = extract_first(root.xpath('//div[@class="compPagination"]/strong/text()'))
    page_url = str(resp.url)
    results = []
    for result in root.xpath('//ol[contains(@class,"searchCenterMiddle")]/li'):
        url = extract_first(result.xpath(".//h3[contains(@class,'title')]//a/@href"))
        if url and 'news.search.yahoo' not in url and 'video.search.yahoo' not in url:
            results.append({'url':url,
                            'title': join_all(result.xpath(".//h3[contains(@class,'title')]//a//text()")),
                            'preview_text': join_all(result.xpath(".//div[@class='compText aAbs']//text()")),
                            'page_url': page_url,
                            'page_num': page_num,
                            'query': query,
                            'source': "Yahoo Search"})
    logger.info(f"Extracted {len(results)} results from page {page_num}. Query: {query}")
    next_page_url = extract_first(root.xpath("//*[@class='next']/@href"))
    if next_page_url:
        logger.info(f"Extracted next page url: {next_page_url}")
    else:
        logger.info(f"No next page url found: {page_url}")
    return results, next_page_url

async def do_search(client: ClientSession, query: str, headers: Dict[str,str],
                    page_min_sleep: int = 0, page_max_sleep: int = 0,
                    max_pages: int = 1000):
    start_url = f'https://search.yahoo.com/search?p={encode_url_str(query)}'
    return await http_search(client=client,
                            query=query,
                            page_url=start_url,
                            headers=headers,
                            parse_page_cb=parse_page,
                            page_min_sleep=page_min_sleep,
                            page_max_sleep=page_max_sleep,
                            max_pages=max_pages)