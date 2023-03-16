from random import randrange
from typing import Union

from vk_api.longpoll import VkEventType
from datetime import datetime, date
from vk_api.exceptions import ApiError

from api import get_vk_api


from db import get_db


MONTS_NAMES = {
    "1": "января",
    "2": "февраля",
    "3": "марта",
    "4": "апреля",
    "5": "мая",
    "6": "июня",
    "7": "июля",
    "8": "августа",
    "9": "сентября",
    "10": "октября",
    "11": "ноября",
    "12": "декабря",
}


def naming_of_years(years, till=True) -> str:
    """addition to years"""
    _years = {1, 21, 31, 41, 51, 61}
    if till is True:
        if years in _years | {71, 81, 91, 101}:
            return f"{years} года"
    else:
        if years in _years:
            return f"{years} год"
        elif years in {
            2,
            3,
            4,
            22,
            23,
            24,
            32,
            33,
            34,
            42,
            43,
            44,
            52,
            53,
            54,
            62,
            63,
            64,
        }:
            return f"{years} года"

    return f"{years} лет"


def get_years(birthday: str):
    """
    Return age by birthday
    """
    if len(birthday.split(".")) == 3:
        try:
            _date = datetime.strptime(birthday, "%d.%m.%Y")
            today = date.today()
            years = today.year - _date.year
            years -= 1 if date.today() < _date else 0
            return years
        except BaseException:
            print("Неверная строка даты рождения")


def get_age(birthday: str) -> str:
    """determining the number of years"""
    try:
        return naming_of_years(get_years(birthday), False)
    except IndexError:
        bdate_splited = birthday.split(".")
        month = MONTS_NAMES.get(bdate_splited[1], "")
        return f"День рождения {int(bdate_splited[0])} {month}."


class User:
    def __init__(self, user_id):
        self.api = get_vk_api()
        self.user_id = user_id

        self.data = self._get_user_data() or {}

        self.name = self.data.get("first_name")

        _bithday = self.data.get("bdate")
        self.age = get_years(_bithday) if _bithday else None

        self.sex = self.data.get("sex")

        _city = self.data.get("city")
        self.city_id = _city["id"] if _city else None
        self.city_title = _city["title"] if _city else None

    def _get_user_data(self):
        try:
            response = self.api.group_connection.users.get(
                user_ids=self.user_id,
                fields="bdate, sex, city, first_name",
            )
            if isinstance(response, list):
                if isinstance(response[0], dict):
                    return response[0]
            print("Bad response %s" % response)
            return {}
        except ApiError as e:
            print(e)
            return {}


class Profile:
    def __init__(self):
        self.age_from = None
        self.age_to = None
        self.city_id = None
        self.city_name = None


class Bot:
    def __init__(self):
        self.api = get_vk_api()
        self.db = get_db()
        self.users = self.api.user_connection.users
        self.photos = self.api.app_connection.photos
        self.database = self.api.app_connection.database
        self.messages = self.api.group_connection.messages
        self.longpoll = self.api.longpoll

        self.user: User = None
        self.profile: Profile = Profile()
        self.found_profiles = []

    def send_msg(self, message: str) -> None:
        """method for sending messages"""
        self._send(message)

    def send_photo(self, message: str, attachments: list[str]) -> None:
        """method for sending photos"""
        self._send(message, ",".join(attachments))

    def _send(self, message, attachments=None):
        self.messages.send(
            user_id=self.user.user_id,
            message=message,
            random_id=randrange(10**7),
            attachment=attachments,
        )

    def input_looking_age(self, age):
        """

        Args:
            age:
        """
        if "-" in age:
            try:
                age = age.split("-")
                _age_from = int(age[0])
                _age_to = int(age[1])

                if _age_from == _age_to:
                    self.profile.age_from = _age_to
                    self.profile.age_to = _age_to
                    message = f" Ищем возраст " \
                              f"{naming_of_years(_age_to, False)}"

                else:
                    self.profile.age_from = _age_from
                    self.profile.age_to = _age_to
                    message = (
                        f" Ищем возраст в пределах от {_age_from} "
                        f"и до {naming_of_years(_age_to)}"
                    )
            except (NameError, ValueError, IndexError):
                message = (
                    " Введен не правильный числовой формат!"
                    " Повторите попытку ввода."
                )
        else:
            self.profile.age_from = int(age)
            self.profile.age_to = int(age)
            message = f" Ищем возраст {naming_of_years(int(age), False)}"

        self.send_msg(message)

    def wait_text(self) -> str:
        for event in self.longpoll.listen():
            print(event.type)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                return event.text

    def wait_start_chat(self):
        for event in self.longpoll.listen():
            print(event.type)
            if event.type == VkEventType.USER_TYPING:
                if not self.user:
                    self.user = User(event.user_id)
                    self.profile = Profile()
                return True

    def get_profile_age(self):
        """
        determine the user's age
        """
        answer = self.wait_text()
        if answer.lower() in {"y", "да", "yes"}:
            self.profile.age_from = self.user.age
            self.profile.age_to = self.user.age
        else:
            self.input_looking_age(answer)

    def get_target_city(self):
        """define city to search"""
        answer = self.wait_text()
        if answer.lower() in {"да", "y", "yes"}:
            if self.user.city_title:
                message = f" Ищем в городе {self.user.city_title}."
                self.profile.city_name = self.user.city_title
                self.profile.city_id = self.user.city_id
                self.send_msg(message)
                return
            else:
                message = (
                    " Ваш город не определён."
                    " Воспользуйтесь поиском по городам."
                )
                self.send_msg(message)

        self.search_city_by_fullname()

    def search_city_by_fullname(self):
        """
        Ищет город по полному совпадению названия.
        Returns:

        """
        while True:
            _error_message = (
                "Ведите плоное название города, к примеру:\n"
                "москва или Москва или МОСКВА"
            )
            self.send_msg(_error_message)
            answer = self.wait_text()
            cities = self.database.getCities(
                country_id=1,
                q=answer.capitalize(),
                need_all=1,
                count=100,
            )
            cities = cities.get("items")
            _error_message = "Город не найден, попробуйте другой город."

            if cities and isinstance(cities, list):
                for city in cities:
                    if city["title"].capitalize() == answer.capitalize():
                        self.profile.city_name = city["title"]
                        self.profile.city_id = city["id"]
                        _message = f"Ищем в городе {self.profile.city_name}"
                        self.send_msg(_message)
                        return
                _error_message += (
                    " Возможно это город не полностью совпал по названию: "
                )
                _cities_names = []
                for _city in cities[:10] if len(cities) > 10 else cities:
                    _cities_names.append(_city.get("title"))
                _error_message += ", ".join(_cities_names)
            self.send_msg(_error_message)

    def looking_for_gender(self):
        """looking for the opposite gender to the user"""
        return 2 if self.user.sex == 1 else 1

    def looking_for_persons(self):
        """search for a person based on the data received"""
        # https://vk.com/dev/users.search

        _fields = "can_write_private_message, city, "\
                  "domain, home_town, is_closed"
        res = self.users.search(
            sort=0,
            city=self.profile.city_id,
            hometown=self.profile.city_name,
            sex=self.looking_for_gender(),
            status=1,
            age_from=self.profile.age_from,
            age_to=self.profile.age_to,
            has_photo=1,
            count=1000,
            fields=_fields,
        )

        for person in res["items"]:
            if not person.get("is_closed"):
                city = person.get("city")
                if city:
                    if city.get("id") == self.profile.city_id:
                        self.found_profiles.append(person["id"])

        self.send_msg(
            f"Найденно {len(self.found_profiles)} "
            f'открытых профилей пользователей {res["count"]}'
        )

    def photo_of_found_person(self, profile_id) -> list[Union[str, None]]:
        """getting a photo of a found person"""
        res = self.photos.get(
            owner_id=profile_id,
            album_id="profile",
            extended=1,
            count=30,
        )

        liked_photos = []
        for item in res["items"]:
            likes = item.get("likes")
            if likes:
                liked_photos.append((likes.get("count", 0), str(item["id"])))

        list_of_ids = sorted(liked_photos, key=lambda x: x[0], reverse=True)
        photo_ids = [_id[1] for _id in list_of_ids]
        attachments = [
            f"photo{profile_id}_{photo_id}"
            for photo_id in photo_ids
        ]

        return attachments

    def get_found_person_id(self):
        """

        Returns:
        """

        # Выбираем из БД просмотренные анкеты.
        _all_profiles = self.db.check_profile(self.user.user_id)
        seen_person = {int(vk_id[0]) for vk_id in _all_profiles}

        # Если сразу после запуска проги набрать Смотреть или S,
        # то ошибка так как в self.found_profiles никого нет.
        try:
            if not seen_person:
                return self.found_profiles[0]
            else:
                for vk_id in self.found_profiles:
                    if vk_id not in seen_person:
                        return vk_id
        except NameError:
            return 0

    def found_person_info(self, profile_id):
        """information about the found person"""

        _fields = (
            "about, activities, bdate, status, "
            "can_write_private_message, city, common_count, "
            "contacts, domain, home_town, interests, movies, "
            "music, occupation"
        )

        res = self.users.get(user_ids=profile_id, fields=_fields)

        _data = res[0]
        first_name = _data.get("first_name")
        last_name = _data.get("last_name")
        age = get_age(_data.get("bdate")) or _data.get("bdate")
        vk_link = "vk.com/" + _data.get("domain")
        city = (
            _data["city"].get("title")
            if _data.get("city")
            else _data.get("home_town")
        )

        response_str = (
            f"{first_name} {last_name}, {age}, " f"Город {city}.\n {vk_link}\n"
        )
        print(response_str)
        return response_str

    def show_found_person(self) -> bool:
        """
        Показывает пользователей из поиска
        """
        profile_id = self.get_found_person_id()

        if not profile_id:
            self.send_msg(
                "Все анекты ранее были просмотрены. "
                "Будет выполнен новый поиск. \n"
                "Измените критерии поиска (возраст, город)."
            )
            return False
        else:
            self.send_msg(self.found_person_info(profile_id))
            self.send_photo(
                "Фото с максимальными лайками",
                self.photo_of_found_person(profile_id),
            )
            self.db.insert(self.user.user_id, profile_id)
            self.send_msg("Нажмите S чтобы посмотреть следующий профиль")
