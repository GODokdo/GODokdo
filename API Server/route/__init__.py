import route.documents
import route.errors
import route.translate
import route.deeplearning
def add_route(api):
    documents.route(api)
    errors.route(api)
    translate.route(api)
    deeplearning.route(api)