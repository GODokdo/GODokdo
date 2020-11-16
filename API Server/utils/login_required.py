from flask import request
from functools import wraps

def login_required(param):
    def b(f):
        @wraps(f)
        @param.response(401, 'Unauthorized')
        def wrapper(*args, **kwargs):
            if request.environ.get('HTTP_X_REAL_IP', request.remote_addr) == '127.0.0.1' or request.headers.get('authorization') == 'godapikey12':
                return f(*args, **kwargs)
            else:
                return {"error": "API KEY가 유효하지 않습니다."}, 401
        return wrapper
    return b