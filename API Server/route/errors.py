from flask import request
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Resource
from utils import *

def route(api):
    errors  = api.namespace('error', description='잘못된 표기에 대한 분류를 확인하거나 추가할 수 있습니다.')
    @errors.route('')
    class Resource_errors(Resource):
        @as_json
        @login_required(errors)
        @errors.response(200, 'OK')
        def get(self):
            with OpenMysql() as conn:
                sql = "SELECT * FROM `error_types`"
                result = conn.execute(sql)
                return {'list': result}, 200

        @as_json
        @login_required(errors)
        @errors.param('code', '오류 코드', 'formData')
        @errors.param('name', '잘못된 표기 분류 이름', 'formData')
        @errors.param('explanation', '잘못된 표기가 왜 잘못되었는지에 대한 상세한 설명', 'formData')
        @errors.response(201, 'OK')
        @errors.response(400, 'Error')
        @errors.response(409, 'Conflict')
        def post(self):
            
            code = postDataGet("code", "").strip()
            name = postDataGet("name", "").strip()
            explanation = postDataGet("explanation", "").strip()
            if (len(code) + len(name) + len(explanation) == 0):
                    return {'error': '모든 칸을 입력해주세요.'}, 400

            with OpenMysql() as conn:
                sql = "INSERT INTO `error_types`(code, name, explanation) VALUES (%s, %s, %s)"
                try:
                    conn.execute(sql, (code, name, explanation))
                    conn.commit()
                    return {
                        'created_code': name
                    }, 201
                except pymysql.err.IntegrityError:
                    return {'error': '이미 등록된 오류 코드입니다.'}, 409
        

    @errors.route('/<int:code>')
    @errors.param('code', '삭제할 오류 코드')
    @errors.response(200, 'OK')
    @errors.response(404, 'Not Found')
    class Resource_errors_delete(Resource):
        @as_json
        @login_required(errors)
        def delete(self, code):
            with OpenMysql() as conn:
                sql = "DELETE FROM `error_types` WHERE `code`=%s"
                conn.execute(sql, (code))
                if (conn.affected_row == 0):
                    return {'error': '존재하지 않는 오류 코드입니다.'}, 404
                else:
                    conn.commit()
                    return {'deleted_code': code}, 200
