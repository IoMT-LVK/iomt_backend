from connexion import NoContent
from flask.views import MethodView

class OperatorView(MethodView):

    def post(self, user, token_info):
        print(self.post.__qualname__)
        return {'id': 1} 

    def put(self, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, user, token_info):
        print(self.get.__qualname__)
        return {'ttt': 123}
