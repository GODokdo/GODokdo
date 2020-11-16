import route.documents
import route.errors
import route.translate
def add_route(api):
    documents.route(api)
    errors.route(api)
    translate.route(api)