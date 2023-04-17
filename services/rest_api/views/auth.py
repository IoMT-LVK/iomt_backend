from connexion import NoContent
from flask.views import MethodView

class AuthView(MethodView):

    def post(self, user, token_info):
        print(self.post.__qualname__)
        return {'id': 1} 

    def get(self, user, token_info):
        print(self.get.__qualname__)
        return {'ttt': 123}
