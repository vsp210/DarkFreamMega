_user_model = None
_round = 12

def set_user_model(model):
    global _user_model
    _user_model = model

def get_user_model():
    global _user_model
    return _user_model

def set_round(round):
    global _round
    _round = round

def get_round():
    global _round
    return _round
