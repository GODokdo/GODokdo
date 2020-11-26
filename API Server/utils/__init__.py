from .as_json import *
from .login_required import *
from .openmysql import *
from flask import request

def postData():
    if request.json is not None:
        return request.json
    return request.form.to_dict(flat=True)

def postDataGet(key, default=None, typedef = None):
    data = postData()
    if key in data:
        if type(data[key]) is str and len(data[key]) == 0:
            return default
        if typedef is None: 
            return data[key]
        else:
            return typedef(data[key])
    else:
        return default

def queryDataGet(key, default=None):
    data = request.args
    if key in data:
        if type(data[key]) is str and len(data[key]) == 0:
            return default

        return data[key]
    else:
        return default