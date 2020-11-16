
# https://developer.mozilla.org/ko/docs/Web/HTTP/Status
import route

from flask import Flask, url_for
from flask_cors import CORS
from flask_restplus import Api

class CustomAPI(Api):
    @property
    def specs_url(self):
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :rtype: str
        '''
        return url_for(self.endpoint('specs'), _external=False)

if __name__ == '__main__':
    app = Flask(__name__)
    authorizations = {
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'authorization'
        }
    }
    cors = CORS(app, resources={r"/*": {"origins": "*"}})
    api = CustomAPI(app, version='1.0', title='GOD API', description='우리나라에 대한 잘못된 표기 사례를 REST API를 통해 관리할 수 있습니다.', authorizations=authorizations, security='apikey') 
    api.app.config['RESTFUL_JSON'] = {
        'ensure_ascii': False
    }
    route.add_route(api)
    app.run(host='0.0.0.0')

