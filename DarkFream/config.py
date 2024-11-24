class DarkFreamConfig:
    """Класс конфигурации для DarkFream.

    Этот класс реализует паттерн Singleton и предоставляет методы для настройки
    пользовательской модели и числа раундов.

    Attributes:
        _instance (DarkFreamConfig): Экземпляр класса, реализующий паттерн Singleton.
        _user_model (type): Пользовательская модель пользователя.
        _round (int): Число раундов, используемое в конфигурации.
    """
    _instance = None
    _user_model = None
    _round = 12

    def __new__(cls):
        """Создает новый экземпляр класса, если он еще не существует.

        Returns:
            DarkFreamConfig: Экземпляр класса DarkFreamConfig.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_user_model(cls, model):
        """Устанавливает пользовательскую модель пользователя.

        Args:
            model (type): Модель пользователя, которая будет использоваться в конфигурации.
        """
        cls._user_model = model

    @classmethod
    def get_user_model(cls):
        """Получает текущую пользовательскую модель пользователя.

        Returns:
            type: Пользовательская модель пользователя, если она установлена, иначе None.
        """
        return cls._user_model

    @classmethod
    def set_round(cls, round):
        """Устанавливает количество раундов для конфигурации.

        Args:
            round (int): Число раундов, которое будет установлено.
        """
        cls._round = round

    @classmethod
    def get_round(cls):
        """Получает текущее количество раундов.

        Returns:
            int: Текущее количество раундов.
        """
        return cls._round
