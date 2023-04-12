from connexion import NoContent
from flask.views import MethodView
import logging

from models.user import User

log = logging.getLogger(__name__)

class UserView(MethodView):

    def post(self, body):
        log.info(f'Submit user registration for {body}')
        usr = User.create(**body)
        return {'id': usr.id} 

    def put(self, id, user, token_info):
        print(self.put.__qualname__)
        return NoContent

    def delete(self, id, user, token_info):
        print(self.delete.__qualname__)
        return NoContent

    def get(self, id, user, token_info):
        user = User.get_by_id(id)
        return jsonify(user)
