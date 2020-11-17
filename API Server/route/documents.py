from flask import request
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Resource
from utils import *
from nltk import tokenize
def preprocessing_sentences(ori_text):
    text = ori_text.strip() # 문서 앞뒤 여백 제거
    text = text.replace("\r","")
    # 일반적으로 해당 텍스트의 줄이 몇번씩 띄워져있는지 확인
    writespace = {}
    space = 0
    for i in text.split("\n")[1:]:
        print("S : ", i.strip())
        if len(i.strip()) != 0: # 내용이 채워진 문장
            if ((space + 1) not in writespace):
                writespace[space + 1] = 1
            else:
                writespace[space + 1] += 1
            print(space + 1)
            space = 0
        else:
            space += 1
    
    default_space = max(writespace, key=writespace.get)
    
    #위의 줄 이상으로 띄워진 단락은 문장이 끝어지지 않았어도 줄바꿈 태그를 제거하지 않음.
    sentences = []
    space = 0
    for i in text.split("\n"):
        print("S : ", i.strip())
        if len(i.strip()) != 0: # 내용이 채워진 문장
            if (default_space < space + 1):
                sentences.append("[#space_tag]")
            sentences.append(i.strip())
            space = 0
        else:
            space += 1
    text = " ".join(sentences) # 모든 문장 이어붙이기
    texts = [i.strip() for i in tokenize.sent_tokenize(text)]
    text = "\n".join(texts).replace(" [#space_tag] ", "\n").replace("[#space_tag] ", "\n")
    return text

def route(api):
    documents  = api.namespace('document', description='잘못된 사실을 기술하고있는 문서를 확인하거나 수정, 추가할 수 있습니다.')

    @documents.route('')
    class Resource_documents(Resource):
        @as_json
        @login_required(documents)
        @documents.response(200, 'OK')
        @documents.param('status', '문서 상태에 따른 검색 필터')
        def get(self):
            with OpenMysql() as conn:
                sql = "SELECT * FROM `document_list` ORDER BY `no` DESC"
                status = request.args.get("status", "")
                if (len(status) > 0):
                    sql = "SELECT * FROM `document_list` WHERE `status`=%s ORDER BY `no` DESC"
                    result = conn.execute(sql, (status))
                else:
                    result = conn.execute(sql)
                for i in range(0,len(result)):
                    if result[i]['errors'] == None:
                        result[i]['errors'] = []
                    else:
                        result[i]['errors'] = [int(i) for i in result[i]['errors'].split(',')]
                return {'list': result}, 200

        @as_json
        @login_required(documents)    
        @documents.param('url', '웹사이트 주소', 'formData')
        @documents.param('title', '본문 타이틀', 'formData')
        @documents.param('contents', '본문 내용', 'formData')
        @documents.response(201, 'OK')
        @documents.response(409, 'Conflict')
        def post(self):
            url = postDataGet("url", None)
            title = postDataGet("title", None)
            contents = postDataGet("contents", None)
            if contents is not None:
                contents = preprocessing_sentences(contents)
            status = "collected"
            with OpenMysql() as conn:
                sql = "INSERT INTO `documents`(url, title, contents, status) VALUES (%s, %s, %s, %s);"
                if url is not None:
                    if len(conn.execute('SELECT no FROM `documents` WHERE `url`=%s',(url))) != 0:
                        return {'error': '이미 등록된 URL 문서입니다.'}, 409
                    if (title is None) != (contents is None):
                        return {'error': 'title과 contents을 모두 채우거나 둘다 채우지 않아야합니다.'}, 400

                    if title is None or contents is None:
                        status = "registered"

                else:
                    status = "collected"
                    if title is None or contents is None:
                        return {'error': 'URL 형식으로 등록하는 경우가 아니라면 제목과 본문을 필수로 추가해야합니다.'}, 400
                conn.execute(sql, (url, title, contents, status))
                conn.commit()
                return {
                    'created_document_no': conn.cursor.lastrowid,
                    'created_document_url': 'https://' + request.host  + '/document/' + str(conn.cursor.lastrowid),
                }, 201

    @documents.route('/<int:no>')
    @documents.param('no', '문서 번호')
    @documents.response(200, 'OK')
    @documents.response(404, 'Not Found')
    class Resource_documents_no(Resource):
        @as_json
        @login_required(documents)
        @documents.param('content-type', '문서의 내용을 string으로 받을지, array로 받을지 결정')
        def get(self, no):
            content_type = queryDataGet('content-type', 'string')
            with OpenMysql() as conn:
                sql = "SELECT * FROM `documents` where `no`=%s"
                result = conn.execute(sql, (no))
                if (len(result) == 0):
                    return {'error' : '문서를 찾지 못함'}, 404

                document = result[0]
                sql = "SELECT `errors`.`no`, `errors`.`code`, name, text, explanation FROM `errors` join `error_types` on `errors`.`code` = `error_types`.`code` where `document_no`=%s"
                result = conn.execute(sql, (no))
                if (content_type == 'array'):
                    document['contents'] = document['contents'].split('\n')
                
                return {'document' : document, 'errors': result, 'content-type':content_type}, 200

        @as_json
        @login_required(documents)
        def delete(self, no):
            with OpenMysql() as conn:
                sql = "DELETE FROM `documents` WHERE `no`=%s"
                conn.execute(sql, (no))
                if (conn.affected_row == 0):
                    return {'error': '삭제할 문서를 찾지 못했습니다.'}, 404
                else:
                    conn.commit()
                    return {'deleted_document_no': no}, 200
        @as_json
        @login_required(documents)
        @documents.param('status', '변경할 상태 데이터')
        @documents.param('title', 'collected 상태로 변경시 문서의 타이틀')
        @documents.param('contents', 'collected 상태로 변경시 문서의 본문')
        def put(self, no):
            # 등록 단계로 바꾼다면.... 상태,내용,에러 검출 내용 모두 초기화
            # 수집됨 단계로 바꾼다면... 상태, (새로운 텍스트), 에러 검출 내용 모두 초기화
            # 라벨링됨 단계로 바꾼다면... 상태, (새로운 텍스트는 있으면 에러 내야함) 정도만..
            # 완료 단계로 바꾸면, 상태만!!!
            can_status = ['registered', 'collected', 'labeled', 'verified']
            data = postData()
            status = postDataGet("status", "")
            title = postDataGet("title", "")
            contents = postDataGet("contents", "")
            
            if len(contents) != 0:
                contents = preprocessing_sentences(contents)

            if len(status) == 0:
                return {'error': 'status는 필수로 입력해야합니다.'}, 400
            if status not in can_status:
                return {'error': "status에는 'registered', 'collected', 'labeled', 'verified' 항목만 사용 가능합니다."}, 400
            if status != 'collected' and len(title) != 0:
                return {'error': '본문 제목 변경은 문서를 collected 단계로 변경할 때만 가능합니다.'}, 400
            if status != 'collected' and len(contents) != 0:
                return {'error': '본문 내용 변경은 문서를 collected 단계로 변경할 때만 가능합니다.'}, 400
                
            if status == 'collected' and len(title) == 0:
                return {'error': 'collected 상태로 변경시 title을 필수로 입력해야합니다.'}, 400
            if status == 'collected' and len(contents) == 0:
                return {'error': 'collected 상태로 변경시 contents를 필수로 입력해야합니다.'}, 400

            with OpenMysql() as conn:
                if len(conn.execute('SELECT no FROM `documents` WHERE `no`=%s',(no))) != 1:
                    return {'error': '내용을 변경할 문서를 찾지 못했습니다.'}, 404
                if status == 'registered':
                    conn.execute("UPDATE `documents` SET `status`=%s, `title`=%s, `contents`=%s WHERE `no`=%s", (status, None, None, no))
                    conn.execute("DELETE FROM `errors` WHERE `document_no`=%s", (no))
                    conn.commit()
                if status == 'collected':
                    conn.execute("UPDATE `documents` SET `status`=%s, `title`=%s, `contents`=%s WHERE `no`=%s", (status, title, contents, no))
                    conn.execute("DELETE FROM `errors` WHERE `document_no`=%s", (no))
                    conn.commit()
                if status == 'labeled':
                    conn.execute("UPDATE `documents` SET `status`=%s WHERE `no`=%s", (status, no))
                    conn.commit()
                if status == 'verified':
                    conn.execute("UPDATE `documents` SET `status`=%s WHERE `no`=%s", (status, no))
                    conn.commit()
            
            return {'success' : True}, 201
                #    conn.execute("UPDATE `documents` SET `updated_time`=CURRENT_TIMESTAMP WHERE `no`=%s", (no))
                #    conn.commit()

    @documents.route('/<int:no>/status')
    @documents.param('no', '문서 번호')
    class Resource_documents_status(Resource):
        @as_json
        @login_required(documents)
        @documents.response(200, 'OK')
        @documents.response(404, 'Not Found')
        def get(self, no):
            with OpenMysql() as conn:
                sql = "SELECT `status`, `updated_time` FROM `documents` where `no`=%s"
                result = conn.execute(sql, (no))
                
                if (len(result) == 0):
                    return {'error' : '문서를 찾지 못함'}, 404
                return result[0], 200

    @documents.route('/<int:no>/error')
    @documents.param('no', '문서 번호')
    class Resource_documents_no_errors(Resource):
        @as_json
        @login_required(documents)
        @documents.response(200, 'OK')
        @documents.response(404, 'Not Found')
        def get(self, no):
            with OpenMysql() as conn:
                sql = "SELECT `errors`.`no`, `errors`.`code`, name, text, explanation FROM `errors` join `error_types` on `errors`.`code` = `error_types`.`code` where `document_no`=%s"
                result = conn.execute(sql, (no))
                return {'errors': result}, 200

        @as_json
        @login_required(documents)
        @documents.param('code', '오류 코드', 'formData')
        @documents.param('text', '문제가 되는 키워드', 'formData')
        @documents.response(201, 'Created')
        @documents.response(404, 'Not Found')
        @documents.response(409, 'Conflict')
        def post(self, no):
            data = postData()
            with OpenMysql() as conn:
                sql = "INSERT INTO `errors`(`document_no`, `code`, `text`) VALUES (%s, %s, %s);"
                try:
                    conn.execute(sql, (no, data['code'], data['text']))
                    created_error_no = conn.cursor.lastrowid
                    conn.execute("UPDATE `documents` SET `updated_time`=CURRENT_TIMESTAMP WHERE `no`=%s", (no))
                    conn.commit()
                    return {
                        'created_error_no': created_error_no
                    }, 201
                except pymysql.err.IntegrityError as e:
                    if e.args[0] == 1452:
                        return {'error': '문서 혹은 오류 식별 코드를 찾을 수 없습니다.'}, 404
                    if e.args[0] == 1062:
                        return {'error': '이미 해당 식별코드로 동일한 키워드가 등록되었습니다.'}, 409
                    
                    return {'error': str(e)}, 500

    @documents.route('/<int:no>/error/<int:error_no>')
    @documents.param('no', '문서 번호')
    @documents.param('error_no', '삭제할 오류 번호')
    class Resource_documents_no_errors_delete(Resource):
        @as_json
        @login_required(documents)
        @documents.response(200, 'OK')
        @documents.response(404, 'Not Found')
        def delete(self, no, error_no):
            with OpenMysql() as conn:
                sql = "DELETE FROM `errors` WHERE `document_no`=%s and `no`=%s"
                conn.execute(sql, (no, error_no))
                if (conn.affected_row == 0):
                    return {'error': '삭제할 내용을 찾지 못했습니다.'}, 404
                else:
                    conn.commit()
                    return {'deleted_error_no': error_no}, 200
