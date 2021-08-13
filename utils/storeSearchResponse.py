from pymongo import MongoClient
import requests
import json

def storeSearchResponse(API_reply_json, query_string,db_url='localhost', db_port=1024, db_name='YtbDataApiSearched'):
    """
    Expecting youtube data api response in json format as the example at the end of the file

    stored mongo db collection schema:
    {
        "query_string": The query string used for querying the youtube data api
        "etag": The item's etag that is used as the unique identifier used by youtube data api
        "kind": The item's kind field in the resopnse body
        "videoId": If the item is video, videoId will be used to store the item's external url suffix
        "channelId": If the item is channel, channelId will be used to store the item's external url suffix
    }

    :param API_reply_json:
    :param db_url:
    :param db_port:
    :param db_name:
    :return:
    """
    db_client = MongoClient(db_url, db_port)
    db = db_client[db_name]

"""
{
  "kind": "youtube#searchListResponse",
  "etag": "NCNYu1SFmEDrXYXnyreASMOU8nw",
  "nextPageToken": "CAUQAA",
  "regionCode": "CA",
  "pageInfo": {
    "totalResults": 1000000,
    "resultsPerPage": 5
  },
  "items": [
    {
      "kind": "youtube#searchResult",
      "etag": "F9y9XS7vrYpMTrqGYlZkk0YmM7I",
      "id": {
        "kind": "youtube#video",
        "videoId": "LYU-8IFcDPw"
      }
    },
    {
      "kind": "youtube#searchResult",
      "etag": "zA3gatPQV30ddxrScJuZ0WpbaHc",
      "id": {
        "kind": "youtube#video",
        "videoId": "uHzzOHUu3sw"
      }
    },
    {
      "kind": "youtube#searchResult",
      "etag": "4RbLu27OicA4x3nrsKWJQUP8_kE",
      "id": {
        "kind": "youtube#video",
        "videoId": "GZmUMSb4UmQ"
      }
    },
    {
      "kind": "youtube#searchResult",
      "etag": "dhd9WsoLVh1FdqKeUdqjJN5i2bc",
      "id": {
        "kind": "youtube#video",
        "videoId": "OZW6bJ_4yag"
      }
    },
    {
      "kind": "youtube#searchResult",
      "etag": "o9HCfPG6y1TQoyi6MNDXlQr__L0",
      "id": {
        "kind": "youtube#video",
        "videoId": "yySl0zHL_FI"
      }
    }
  ]
}

"""
