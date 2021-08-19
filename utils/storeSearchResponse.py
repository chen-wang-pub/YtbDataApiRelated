from pymongo import MongoClient, DESCENDING

def storeSearchResponse(api_reply_json, query_string,db_url='localhost', db_port=1024, db_name='YtbDataApiSearched',
                        col_name='YtbSearchRecord'):
    """
    Expecting youtube data api response in json format as the example at the end of the file

    stored mongo db collection schema:
    {
        "query_string": The query string used for querying the youtube data api
        "etag": The item's etag that is used as the unique identifier used by youtube data api
        "kind": The item's kind field in the resopnse body
        "item_id": The video id or channel id of the item. It's the suffix of the youtube video
    }

    api example: https://youtube.googleapis.com/youtube/v3/search?q=xxxx&key=xxxx
    https://developers.google.com/youtube/v3/docs/search#resource
    :param API_reply_json:
    :param db_url:
    :param db_port:
    :param db_name:
    :return:
    """
    # TODO: Need to split the response handle with the document upload
    db_client = MongoClient(db_url, db_port)
    db = db_client[db_name]
    collection = db[col_name]
    collection.create_index([('etag', DESCENDING)], unique=True)

    searched_items = api_reply_json['items']
    for item in searched_items:
        etag = item['etag']
        kind = item['id']['kind']
        if 'videoId' in item['id']:
            item_id = item['id']['videoId']
        elif 'channelId':
            item_id = item['id']['channelId']
        elif 'playlistId':
            item_id = item['id']['playlistId']

        # TODO: need to rewrite the following part with the $addtoset updateone upsert, and add test to it
        # TODO: Add check that the insert succeeded and return the result
        # TODO: Add error handling and add testing


        cursor = collection.find({'etag': etag}, {'query_string': 1, '_id':0})
        doc = next(cursor, None)
        if doc:
            current_queries = doc['query_string']
            if query_string not in current_queries:
                current_queries.append(query_string)
        else:
            current_queries = [query_string]
        final_record = {'etag': etag, 'kind': kind, 'item_id': item_id, 'query_string': current_queries}
        collection.replace_one({"etag": etag}, final_record, upsert=True)


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
