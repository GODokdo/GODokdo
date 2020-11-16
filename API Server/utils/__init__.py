from .as_json import *
from .login_required import *
from .openmysql import *
from flask import request

def postData():
    if request.json is not None:
        return request.json
    return request.form.to_dict(flat=True)

def postDataGet(key, default=None):
    data = postData()
    if key in data:
        return data[key]
    else:
        return default