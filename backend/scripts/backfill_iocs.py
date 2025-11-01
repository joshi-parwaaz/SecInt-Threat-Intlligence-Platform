from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid
import json

client = MongoClient('mongodb://localhost:27017')
db = client['secint']
col = db['iocs']

mapping = {
    'md5': 'filehash', 'sha1': 'filehash', 'sha256': 'filehash',
    'ipv4': 'ip', 'domain': 'domain', 'url': 'url', 'cve': 'cve', 'email': 'email'
}

updated = 0
errors = 0

cursor = col.find({})
for doc in cursor:
    try:
        update = {}
        # correlation_id
        if 'correlation_id' not in doc or not doc.get('correlation_id'):
            update['correlation_id'] = str(uuid.uuid4())
        # ioc_category
        itype = doc.get('ioc_type')
        if 'ioc_category' not in doc or not doc.get('ioc_category'):
            update['ioc_category'] = mapping.get(itype, 'other')
        # last_updated
        if 'last_updated' not in doc or not doc.get('last_updated'):
            if doc.get('first_seen'):
                update['last_updated'] = doc.get('first_seen')
            else:
                update['last_updated'] = doc.get('_id').generation_time
        # abuse_score from sources
        if ('abuse_score' not in doc or doc.get('abuse_score') in (None, 0)) and doc.get('sources'):
            abuse = doc['sources'].get('abuseipdb')
            if abuse and abuse.get('abuse_confidence_score') is not None:
                update['abuse_score'] = abuse.get('abuse_confidence_score')
        # VT normalization
        vt_d = doc.get('vt_detections')
        vt_rate = doc.get('vt_detection_rate')
        if vt_d:
            try:
                if isinstance(vt_d, str) and '/' in vt_d:
                    parts = vt_d.split('/')
                    detected = int(parts[0])
                    total = int(parts[1]) if int(parts[1])>0 else 0
                    update['vt_detections'] = f"{detected}/{total}"
                    update['vt_detection_rate'] = (detected/total) if total>0 else 0.0
                elif isinstance(vt_d, (list,tuple)) and len(vt_d)==2:
                    detected=int(vt_d[0]); total=int(vt_d[1])
                    update['vt_detections'] = f"{detected}/{total}"
                    update['vt_detection_rate'] = (detected/total) if total>0 else 0.0
            except Exception:
                update['vt_detections'] = "0/0"
                update['vt_detection_rate'] = 0.0
        else:
            # ensure fields exist
            if 'vt_detections' not in doc:
                update['vt_detections'] = "0/0"
            if 'vt_detection_rate' not in doc:
                update['vt_detection_rate'] = 0.0

        if update:
            col.update_one({'_id': doc['_id']}, {'$set': update})
            updated += 1
    except Exception as e:
        errors += 1
        print(f"Error updating doc {doc.get('_id')}: {e}")

print(json.dumps({'updated': updated, 'errors': errors}, indent=2))
