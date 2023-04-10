from connexion import NoContent
from flask.views import MethodView

from models.user import User

class UserView(MethodView):

    def post(self, user=None, token_info=None):
        print(self.post.__qualname__)
        return {'id': 1} 

    def put(self, id, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, id, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, id, user, token_info):
        user = User.get_by_id(id)
        return jsonify(user)
