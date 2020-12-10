from typing import List
from bs4 import BeautifulSoup
import requests
import logging
from bson.objectid import ObjectId
from pymongo.collection import Collection

URL = "https://www.avito.ru"

logging.basicConfig(filename='advertisement_scrapper.log', level=logging.DEBUG)


def get_top_advertisements(region: str, query: str) -> List[str]:
    logging.info(f"Posted a top advertisements request for {region} {query}")
    r = requests.get(f"{URL}/{region}?q={query}")
    soup = BeautifulSoup(r.text, features="html.parser")
    advertisements = soup.find_all("div", {"data-marker": "item"})
    if not advertisements:
        return []
    return [f"{URL}{advertisement.find('a')['href']}" for advertisement
            in advertisements[:min(5, len(advertisements))]]


def scrap_top_advertisements(id: ObjectId, region: str,
                             query: str, collection: Collection) -> None:
    logging.info(
        f"Started advertisements scrapping for {id}, {region}, {query}")
    top_advertisements = get_top_advertisements(region, query)
    logging.info(f"Received {top_advertisements} for {id}, {region}, {query}")
    collection.update_one(
        {"_id": id},
        {'$set': {'top_advertisements': top_advertisements}})
    logging.info(
        f"Advertisements scrapping for {id}, {region}, {query} finished")
