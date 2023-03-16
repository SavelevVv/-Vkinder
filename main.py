from bot import naming_of_years, Bot

# from db import *
START_MSG = (
    " Бот готов к поиску, наберите: \n "
    " Поиск или F - Поиск людей. \n"
    " Удалить или D - удаляет старую БД и создает новую. \n"
    " Смотреть или S - просмотр следующей записи в БД."
)

bot = Bot()


def login_user():
    if bot.wait_start_chat():
        bot.send_msg(START_MSG)


def search_dialog():
    default_message = (
        " Bведите возраст поиска, "
        "на пример от 21 года и до 35 лет, "
        "в формате : 21-35 (или 21 конкретный возраст 21 год)."
    )

    if bot.user.age:
        message = (
            f"Ваш возраст: {naming_of_years(bot.user.age)} "
            f"отправьте y что бы искать человека "
            f"своего возрастаn\n или \n"
        )
        bot.send_msg(message + default_message)
    else:
        message = "Ваша дата рождения неизвестна! \n"
        bot.send_msg(message + default_message)

    while bot.profile.age_from is None or bot.profile.age_to is None:
        # воодим возраст поиска
        bot.get_profile_age()

    message = (
        "Введите: Да/y/yes - поиск будет произведен в городе"
        "указанном в профиле. \n"
        "Для поиска в другом городе введите Нет/n/no"
    )
    bot.send_msg(message)
    while bot.profile.city_id is None or bot.profile.city_name is None:
        # выбираем город поиска
        bot.get_target_city()

    # выводит список в чат найденных людей и добавляет их в базу данных.
    bot.looking_for_persons()

    # выводит в чат инфо одного человека из базы данных.
    bot.show_found_person()


def drop_all():
    bot.db.delete(bot.user.user_id)
    bot.send_msg(' База данных очищена! Сейчас наберите "Поиск" или F ')
    bot.user = None
    bot.profile = None


def print_profile():
    if bot.get_found_person_id() != 0:
        bot.show_found_person()
    else:
        bot.send_msg(" В начале наберите Поиск или f.  ")


def bad_request():
    bot.send_msg(
        "Не понимаю вас, "
        "попробуте что то из списка моих команд "
        f"\n {START_MSG[34:]}"
    )


def main():
    login_user()

    while True:
        try:
            answer = bot.wait_text().lower()

            if answer == "поиск" or answer == "f":
                search_dialog()

            elif answer == "удалить" or answer == "d":
                drop_all()
                return

            elif answer == "смотреть" or answer == "s":
                print_profile()
            else:
                bad_request()

        except BaseException as e:
            message = "Что то пошло не так, повторите запрос ещё раз"
            bot.send_msg(f"{e}\n{message}\n")
            bot.send_msg(START_MSG)
            raise e


if __name__ == "__main__":
    while True:
        main()
