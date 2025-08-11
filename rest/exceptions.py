class ApiNotRespondedException(Exception):
    """Ошибка бизнес-логики, если внешний сервис не отвечает"""

    pass


class HeroNotFound(Exception):
    """Ошибка бизнес-логики, если герой не был найден"""

    pass
