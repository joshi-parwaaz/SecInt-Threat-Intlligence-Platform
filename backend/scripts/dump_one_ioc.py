from pymongo import MongoClient
import json

c = MongoClient('mongodb://localhost:27017')
col = c['secint']['iocs']
doc = col.find_one({})
print(json.dumps({k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v for k,v in doc.items()}, indent=2))
