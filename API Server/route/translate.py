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
            src = request.args.get('src', None)
            dest = request.args.get('dest', 'ko')
            text = request.args.get('text', "")
            if src is None:
                translated = google_translate(text, dest=dest)
            else:
                translated = google_translate(text, src=src, dest=dest)
            return {
                "src": translated.src,
                "dest": translated.dest,
                "origin": translated.origin, 
                "translated": translated.text,
                "pronunciation": translated.pronunciation
            }, 200