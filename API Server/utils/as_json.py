import json
from flask import Response
from functools import wraps
from datetime import date, datetime

def json_default(value): 
    if isinstance(value, datetime): 
        return value.strftime('%Y-%m-%d %H:%M:%S') 
    raise TypeError('not JSON serializable')


def as_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        res = f(*args, **kwargs)
        data = json.dumps(res[0], ensure_ascii=False, default = json_default).encode('utf8')
        return Response(data, content_type='application/json; charset=utf-8', status=res[1])

    return decorated_function