from connexion.jsonifier import JSONEncoder
import jwt

def decode_token(token):
    return jwt.decode(token, 'TODO change', algorithms=['HS256'])

def not_found_handler(exception):
    return {
        "title": "Object doesn't found",
        "description": str(exception),
    }, 404

class SerializeJSONEncoder(JSONEncoder):
    def default(obj):
        try:
            serialized = obj.serialize()
        except AttributeError:
            pass
        else:
            return serialized
        return super().default(obj)

