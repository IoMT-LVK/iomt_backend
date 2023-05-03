from connexion import problem


class BaseApiError(Exception):
    """Base error for handling"""
    code: int
    title: str
    detail: str
    type: str  # absolute URI to description of problem

class CantSendEmailError(BaseApiError):
    """Server cant send email for some reason"""
    code =  424
    title = "Can't send email"
    detail = "Server can't send registration email to {email_address}."


def error_handler(exception):
    return exception.problem()
    exc
    if type(exception) is LoginExistsError:
        title = "User login should be unique"
        code = 409
    else:
        title = "Exception unhandled"
        code = 500
    return {
        'title': title,
        'description': str(exception),
    }, code

def init_app(app):
    app.add_error_handler(BaseApiError, error_handler)
