_user_model = None
_round = 12
_handler = None


def set_user_model(model):
    global _user_model
    _user_model = model

def get_user_model():
    global _user_model
    return _user_model

def set_handler(handler):
    global _handler
    _handler = handler

def get_handler():
    global _handler
    return _handler

def set_round(round):
    global _round
    _round = round

def get_round():
    global _round
    return _round
