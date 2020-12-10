from typing import List, Mapping, Union
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException
import os
from bson.errors import InvalidId
from bson.objectid import ObjectId
from bisect import bisect_left, bisect_right
from advertisement_scrapper import scrap_top_advertisements
import threading
import logging

logging.basicConfig(filename="app.log", level=logging.DEBUG)

client = MongoClient(os.environ["MONGODB_HOSTNAME"], 27017)
collection = client.counts_database.counts_collection
app = FastAPI()


@app.post("/add")
async def add(region: str, query: str) -> str:
    """
    Adds (region, query) pair to the database.

    :param region: Region name, lowercase latin letters.
    :param query: Query string.
    :returns: ID of (region, query) in the database.
    :raises HTTPException: (region, query) is already in database
    """
    logging.info(f"/add {region} {query}")
    post = collection.find_one({"region": region, "query": query})
    if post:
        logging.info(
            f"{region}, {query} item already in database, ID={post['_id']}")
        raise HTTPException(
            status_code=400, detail=f"Iteam already in database, ID={post['_id']}")

    post_id = collection.insert_one(
        {"region": region, "query": query,
         "counts": [], "top_advertisements": []}
    ).inserted_id

    logging.info(
        f"Starting a thread for top advertisements scrapper, id={post_id}")
    scrapper_thread = threading.Thread(
        target=scrap_top_advertisements, args=(
            post_id, region, query, collection)
    )
    scrapper_thread.start()
    return str(post_id)


@app.get("/stat")
async def stat(id: str, start: float, end: float) -> List[Union[Mapping[str, float],
                                                                Mapping[str, int]]]:
    """
    Retrieves advertisements counts and timestams for a given period, ID.

    :param id: (region, query) ID in database.
    :param start: Start of the period, timestamp.
    :param end: End of the period, timestamp.
    :returns: Array of {"timestamp" : float, "count" : int} objects.
              The considered period is [start, end].
    :raises HTTPException: ID is invalid.
    :raises HTTPException: (region, query) with given ID not found.
    """
    logging.info(f"/stat {id} {start} {end}")
    try:
        id = ObjectId(id)
    except InvalidId:
        logging.error(f"Invalid ID={id}, failed to retrieve counts")
        raise HTTPException(status_code=400, detail=f"Invalid ID={id}")

    post = collection.find_one({"_id": id})
    if not post:
        logging.error(f"Item not found {id}, failed to retrieve counts")
        raise HTTPException(status_code=404, detail="Item not found")

    counts = post["counts"]
    logging.info(f"Successfully retrieved counts array for {id}")
    timestamps = [x["timestamp"] for x in counts]
    l = bisect_left(timestamps, start)
    r = bisect_right(timestamps, end)
    return counts[l:r]


@app.get("/top5")
async def top5(id: str) -> List[str]:
    """
    Retrieves top 5 advertisments for given ID.

    :param id: (region, query) ID in database.
    :returns: List of hrefs for top5 advertisements, in order.
    :raises HTTPException: ID is invalid.
    :raises HTTPException: (region, query) with given ID not found.
    """
    logging.info(f"/top5 {id}")
    try:
        id = ObjectId(id)
    except InvalidId:
        logging.error(f"Invalid ID={id}, failed to retrieve top5")
        raise HTTPException(status_code=400, detail=f"Invalid ID={id}")
    post = collection.find_one({"_id": id})
    if not post:
        logging.error(
            f"Item not found {id}, failed to retrieve top advertisements")
        raise HTTPException(status_code=404, detail="Item not found")

    return post["top_advertisements"]
