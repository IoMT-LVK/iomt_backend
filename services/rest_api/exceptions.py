from peewee import DoesNotExist

class BaseApiError(Exception):
    """Base error for handling"""

class LoginExistsError(BaseApiError):
    """User should have unique login"""

class CantSendEmailError(BaseApiError):
    """Server cant send email for some reason"""

def error_handler(exception):
    if type(exception) is LoginExistsError:
        title = "User login should be unique"
        code = 409
    elif type(exception) is DoesNotExist:
        title = "Can't find ibject with such ID"
        code = 404
    else:
        title = "Exception unhandled"
        code = 500
    return {
        'title': title,
        'description': str(exception),
    }, code
