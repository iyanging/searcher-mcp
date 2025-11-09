# Copyright (c) 2025 iyanging
#
# deepReSearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
#
# See the Mulan PSL v2 for more details.

import asyncio
from random import randint
from typing import TypedDict, cast
from urllib.parse import quote_plus

import lxml.html
from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox
from fastmcp import FastMCP
from playwright.async_api import Browser

mcp = FastMCP(
    "Searcher MCP Server",
    instructions="This server provides web search tools.",
)


class Document(TypedDict):
    title: str
    link: str
    snippet: str


GOOGLE_SEARCH_MAX_COUNT_PER_PAGE = 10


@mcp.tool
async def google_search(query: str, max_result_count: int) -> list[Document]:
    async with (
        cast(
            Browser,
            AsyncCamoufox(
                os="windows",
                screen=Screen(max_width=1920, max_height=1080),
                locale="en-US",
                humanize=True,
                headless=True,
            ),
        ) as browser,
        await browser.new_context() as ctx,
        await ctx.new_page() as page,
    ):
        documents: list[Document] = []

        # "start" starts from 0
        for start in range(0, max_result_count, GOOGLE_SEARCH_MAX_COUNT_PER_PAGE):
            if start > 0:
                url = (
                    f"https://www.google.com/search?q={quote_plus(query)}&start={start}"
                )
            else:  # simulate startup
                url = f"https://www.google.com/search?q={quote_plus(query)}"

            _ = await page.goto(url)

            await page.wait_for_selector('div[data-snhf="0"]')

            html = lxml.html.fromstring(await page.content())

            for title_and_link_div, snippet_div in zip(
                html.cssselect('div[data-snhf="0"]'),
                html.cssselect('div[data-sncf="1"]'),
            ):
                title_el = title_and_link_div.cssselect("h3")
                if not title_el:
                    continue

                link_el = title_and_link_div.cssselect("a")
                if not link_el:
                    continue

                snippet_el = snippet_div.cssselect("*")
                if not snippet_el:
                    continue

                documents.append(
                    {
                        "title": title_el[0].text_content().strip(),
                        "link": link_el[0].get("href") or "",
                        "snippet": snippet_el[0].text_content().strip(),
                    }
                )

            await asyncio.sleep(randint(1500, 2500) / 1000)

        return documents
