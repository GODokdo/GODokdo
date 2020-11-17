from flask import request
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Resource
from utils import *
from googletrans import Translator
COUNT = 0
translator = None
def newTranslator():
    print("retry: translate")
    global COUNT
    while True:
        translator = Translator(service_urls=['translate.google.com'])
        try:
            trial = translator.detect('Hello there')  
            return translator              
        except Exception as e:
            COUNT+=1

def google_translate(*args, **kwargs):
    global translator
    if translator is None:
        translator = newTranslator()
    try:
        return translator.translate(*args, **kwargs)
    except Exception as e:
        translator = newTranslator()
        return translator.translate(*args, **kwargs)

def route(api):
    translate  = api.namespace('translate', description='주어진 문장을 번역합니다.')
    
    @translate.route('/from/google')
    class Resource_translate(Resource):
        @as_json
        @login_required(translate)
        @translate.param('src', '출발 언어')
        @translate.param('dest', '도착 언어')
        @translate.param('text', '번역할 문장')
        @translate.response(200, 'OK')
        def get(self):
            src = queryDataGet('src', default='en')
            dest = queryDataGet('dest', default='ko')
            text = queryDataGet('text', default="").strip()
            if len(text) == 0:
                return {
                    "src": src,
                    "dest": dest,
                    "origin": "", 
                    "translated": ""
                }, 200
            with OpenMysql() as conn:
                result = conn.execute("SELECT `translated` FROM `translate` where `api`=%s and `src`=%s and `dest`=%s and `origin`=%s", ('google',src,dest,text))
                if len(result) != 0:
                    return {
                        "src": src,
                        "dest": dest,
                        "origin": text, 
                        "translated": result[0]['translated']
                    }, 200
                translated = google_translate(text, src=src, dest=dest)
                sql = "INSERT INTO `translate`(`api`, `src`, `dest`, `origin`, `translated`) VALUES (%s, %s, %s, %s, %s)"
                if text != translated.text:
                    result = conn.execute(sql, ('google', src, dest, text, translated.text))
                    conn.commit()
                return {
                    "src": translated.src,
                    "dest": translated.dest,
                    "origin": translated.origin, 
                    "translated": translated.text
                }, 200