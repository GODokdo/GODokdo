from flask import request
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Resource
from utils import *

def route(api):
    statistics  = api.namespace('statistics', description='문서, 에러 등의 통계 정보를 확인할 수 있습니다.')
    
    @statistics.route('/errors')
    class Resource_statistics(Resource):
        @as_json
        @login_required(statistics)
        @statistics.response(200, 'OK')
        def get(self):
                with OpenMysql() as conn:
                    sql = "SELECT * FROM `count_errors`"
                    result = conn.execute(sql)
                    return {'list': result}, 200
