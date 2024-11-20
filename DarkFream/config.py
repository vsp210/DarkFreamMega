class DarkFreamConfig:
    _instance = None
    _user_model = None
    _round = 12

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_user_model(cls, model):
        cls._user_model = model

    @classmethod
    def get_user_model(cls):
        return cls._user_model

    @classmethod
    def set_round(cls, round):
        cls._round = round

    @classmethod
    def get_round(cls):
        return cls._round
