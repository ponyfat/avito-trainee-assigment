from bs4 import BeautifulSoup
import requests
import time
from pymongo import MongoClient
import os
import logging

URL = "https://www.avito.ru"
QUESTIONING_INTERVAL = 3 * 60  # time between two counts scrappings, seconds

logging.basicConfig(filename="scrapper.log", level=logging.DEBUG)
client = MongoClient(os.environ["MONGODB_HOSTNAME"], 27017)
collection = client.counts_database.counts_collection


def get_advertisements_count(region: str, query: str) -> int:
    r = requests.get(f"{URL}/{region}?q={query}")
    soup = BeautifulSoup(r.text, features="html.parser")
    count = soup.find("span", {"data-marker": "page-title/count"})
    if count:
        logging.info(
            f"Successfully got count for {region}, {query} : {count.text}"
        )
        count = count.text.replace(" ", "")
        return int(count)
    else:
        logging.error(f"Impossible to get count for {region}, {query}")
        return -1


def scrap_advertisements_counts() -> None:
    for post in collection.find():
        count = get_advertisements_count(post["region"], post["query"])
        timestamp = time.time()
        collection.update_one(
            {"_id": post["_id"]},
            {"$push": {"counts": {"timestamp": timestamp, "count": count}}},
        )


if __name__ == "__main__":
    while True:
        logging.info(
            "Executing scrapper, current time : {}".format(time.ctime()))
        scrap_advertisements_counts()
        time.sleep(QUESTIONING_INTERVAL)
