from urllib.parse import urlparse

import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard.bs4_parser import BS4Parser

# {'title': 'Danger.in.the.House.2022.720p.WEB.h264-BAE', 'title_detail': {'type': 'text/plain', 'language': None, 'base': '', 'value': 'Danger.in.the.House.2022.720p.WEB.h264-BAE'}, 'id': 'https://example.com/details/random-guid', 'guidislink': True, 'link': 'https://example.com/getnzb?id=random-guid.nzb&r=1260abc930e0cebbbfc687a42a7c1450', 'links': [{'rel': 'alternate', 'type': 'text/html', 'href': 'https://example.com/getnzb?id=random-guid.nzb&r=1260abc930e0cebbbfc687a42a7c1450'}, {'length': '1962145316', 'type': 'application/x-nzb', 'href': 'https://example.com/getnzb?id=random-guid.nzb&r=1260abc930e0cebbbfc687a42a7c1450', 'rel': 'enclosure'}], 'comments': 'https://example.com/details/random-guid#comments', 'published': 'Tue, 30 Aug 2022 01:30:51 +0200', 'published_parsed': time.struct_time(tm_year=2022, tm_mon=8, tm_mday=29, tm_hour=23, tm_min=30, tm_sec=51, tm_wday=0, tm_yday=241, tm_isdst=0), 'summary': 'Danger.in.the.House.2022.720p.WEB.h264-BAE', 'summary_detail': {'type': 'text/html', 'language': None, 'base': '', 'value': 'Danger.in.the.House.2022.720p.WEB.h264-BAE'}, 'newznab_attr': {'name': 'size', 'value': '1962145316'}}
#   <item>
#    <title>Danger.in.the.House.2022.720p.WEB.h264-BAE</title>
#    <guid isPermaLink="true">https://example.com/details/random-guid</guid>
#    <link>https://example.com/getnzb?id=random-guid.nzb&amp;r=1260abc930e0cebbbfc687a42a7c1450</link>
#    <comments>https://example.com/details/random-guid#comments</comments>
#    <pubDate>Tue, 30 Aug 2022 01:30:51 +0200</pubDate>
#    <description>Danger.in.the.House.2022.720p.WEB.h264-BAE</description>
#    <enclosure url="https://example.com/getnzb?id=random-guid.nzb&amp;r=1260abc930e0cebbbfc687a42a7c1450" length="1962145316" type="application/x-nzb"/>
#    <newznab:attr name="category" value="5010"/>
#    <newznab:attr name="size" value="1962145316"/>
#   </item>


def getFeed(url, params=None, request_hook=None):
    def check_link(link):
        return urlparse(link).netloc == urlparse(url).netloc or validators.url(link) == True

    items = []
    try:
        data = request_hook(url, params=params, returns="text", timeout=30)
        if not data:
            raise Exception

        with BS4Parser(data, language="xml") as feed:
            try:
                torznab = feed.find("server").get("title") == "Jackett"
            except AttributeError:
                try:
                    torznab = "xmlns:torznab" in feed.rss.attrs
                except AttributeError:
                    torznab = False

            for item in feed("item"):
                try:
                    title = item.title.get_text(strip=True)
                    download_url = None
                    if item.link:
                        if check_link(item.link.get_text(strip=True)):
                            download_url = item.link.get_text(strip=True)
                        elif check_link(item.link.next.strip()):
                            download_url = item.link.next.strip()

                    if not download_url and item.enclosure and check_link(item.enclosure.get("url", "").strip()):
                        download_url = item.enclosure.get("url", "").strip()

                    if not (title and download_url):
                        continue

                    seeders = leechers = None
                    item_size = item.size.get_text(strip=True) if item.size else -1
                    for attr in item.find_all(["newznab:attr", "torznab:attr"]):
                        item_size = attr["value"] if attr["name"] == "size" else item_size
                        seeders = try_int(attr["value"]) if attr["name"] == "seeders" else seeders
                        leechers = try_int(attr["value"]) if attr["name"] == "peers" else leechers

                    if not item_size or (torznab and (seeders is None or leechers is None)):
                        continue

                    size = convert_size(item_size) or -1

                    result = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers}
                    items.append(result)
                except Exception:
                    continue
    except Exception as error:
        logger.debug(f"RSS error: {error}")

    return {"entries": items}
