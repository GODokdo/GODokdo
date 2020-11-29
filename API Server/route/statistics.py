from flask import request
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Resource
from utils import *

def route(api):
    statistics  = api.namespace('statistics', description='문서, 에러 등의 통계 정보를 확인할 수 있습니다.')
    @statistics.route('/document')
    class Resource_statistics_document(Resource):
        @as_json
        @login_required(statistics)
        @statistics.response(200, 'OK')
        def get(self):
                with OpenMysql() as conn:
                    sql = "SELECT `status`, count(*) as 'count' from `documents` group by `status`"
                    result = conn.execute(sql)
                    total = 0
                    document_count = {}
                    for i in result:
                        total += i['count']
                    can_status = ['registered', 'collected', 'labeled', 'verified']
                    for i in can_status:
                        find_status = False
                        for j in result:
                            if j['status'] == i: find_status = True

                        if not find_status:
                            result.append({'status':i, 'total':0})

                    return {'list': result, 'total': total}, 200


    @statistics.route('/document/by-date')
    class Resource_statistics_document_date(Resource):
        @as_json
        @login_required(statistics)
        @statistics.response(200, 'OK')
        def get(self):
            with OpenMysql() as conn:
                sql = "SELECT * from count_documents_date ORDER BY date DESC"
                result = conn.execute(sql)
                total = 0
                document_count = {}
                for i in result:
                    if (i['date'] not in document_count):
                        document_count[i['date']] = {'date': i['date'], 'error': 0, 'total': 0}
                    if (i['in_error'] == 1):
                        document_count[i['date']]['error'] = i['count']

                    document_count[i['date']]['total'] += i['count']
                return {'list': list(document_count.values())[:7]}, 200

    @statistics.route('/error')
    class Resource_statistics_errors(Resource):
        @as_json
        @login_required(statistics)
        @statistics.response(200, 'OK')
        def get(self):
                with OpenMysql() as conn:
                    sql = "SELECT * FROM `count_errors`"
                    result = conn.execute(sql)
                    total = 0
                    for i in result:
                        total += i['count']
                    return {'list': result, 'total': total}, 200
