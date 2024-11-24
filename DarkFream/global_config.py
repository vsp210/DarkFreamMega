_user_model = None
_round = 12
_handler = None

def set_user_model(model):
    """Устанавливает модель пользователя.

    Args:
        model: Модель пользователя, которую необходимо установить.
    """
    global _user_model
    _user_model = model

def get_user_model():
    """Получает текущую модель пользователя.

    Returns:
        Модель пользователя, установленная ранее.
    """
    global _user_model
    return _user_model

def set_handler(handler):
    """Устанавливает обработчик.

    Args:
        handler: Обработчик, который необходимо установить.
    """
    global _handler
    _handler = handler

def get_handler():
    """Получает текущий обработчик.

    Returns:
        Обработчик, установленный ранее.
    """
    global _handler
    return _handler

def set_round(round):
    """Устанавливает значение округления.

    Args:
        round (int): Значение, до которого необходимо округлять.
    """
    global _round
    _round = round

def get_round():
    """Получает текущее значение округления.

    Returns:
        int: Значение округления, установленное ранее.
    """
    global _round
    return _round
