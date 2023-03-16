from vk_api.vk_api import VkApiMethod
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll

from config import (
    group_token,
    app_id,
    group_id,
    service_key,
    user_login,
    user_password,
)


class Api:
    def __init__(self):
        self._user_session = self._login_user()
        self.user_connection: VkApiMethod = self._user_session.get_api()

        self._app_session = VkApi(token=service_key, app_id=app_id)
        self.app_connection: VkApiMethod = self._app_session.get_api()

        self._group_session = VkApi(token=group_token, app_id=app_id)
        self.group_connection: VkApiMethod = self._group_session.get_api()

        self.longpoll = VkLongPoll(vk=self._group_session, group_id=group_id)

    @staticmethod
    def _auth_handler():
        """
        При двухфакторной аутентификации вызывается эта функция.
        """
        key = input("Enter authentication code: ")
        remember_device = True
        return key, remember_device

    def _login_user(self, login=user_login, password=user_password):
        """
        Пример обработки двухфакторной аутентификации
        """
        vk_session = VkApi(
            login=login,
            password=password,
            # функция для обработки двухфакторной аутентификации
            auth_handler=self._auth_handler,
        )
        vk_session.auth()
        return vk_session


MY_API = Api()


def get_vk_api():
    return MY_API
