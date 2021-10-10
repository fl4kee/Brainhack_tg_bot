import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from database_funcs import find_suitable, pet_places_collection, get_location_triplets, get_locations, get_categories


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

tg_token = '1641863400:AAHP31Sn6MJHlBdH69FbBktaCdjwBoA-8I0'
GREETINGS, CHOOSING_CITY, CHOOSING_CATEGORY = range(3)
categories = []
locations = []
location_triplets = []
page_counter = 0


def start(update: Update, _: CallbackContext) -> int:
    global categories
    global locations
    global location_triplets
    categories =get_categories()
    locations = get_locations()
    location_triplets = get_location_triplets(locations)
    hello_choice = [['Выбрать свой город'], ['Завершить работу Petplaces Bot']]
    hello_markup = ReplyKeyboardMarkup(hello_choice, one_time_keyboard=True)
    update.message.reply_text(
        "Привет! Petplaces Bot - поможет Вам найти в своём городе людей, готовых помочь с уходом за питомцами!\n"
        "Для начала нам нужно узнать, где Вы живёте.", reply_markup=hello_markup)
    return GREETINGS


def choosing_city(update: Update, context: CallbackContext) -> int:
    global page_counter
    page_counter = 0
    update.message.reply_text("Наш сервис пока что работает лишь в нескольких городах. Выберите свой город, нажав на одну из кнопок ниже.\n")
    return begin_choosing_city(update, context)


def begin_choosing_city(update: Update, _: CallbackContext) -> int:
    global page_counter
    print(page_counter)
    begin_location_choice = [*location_triplets[0], ['вперёд-->']]
    begin_location_markup = ReplyKeyboardMarkup(begin_location_choice, one_time_keyboard=True)
    update.message.reply_text(
        "Навигация по списку городов осуществляется с помощью кнопок '<--назад' и 'вперёд-->'", reply_markup=begin_location_markup)
    return CHOOSING_CITY


def mid_choosing_city(update: Update, _: CallbackContext) -> int:
    global page_counter

    middle_location_choice = [*location_triplets[page_counter], ['<--назад', 'вперёд-->']]
    middle_location_markup = ReplyKeyboardMarkup(middle_location_choice, one_time_keyboard=True)
    update.message.reply_text("Навигация по списку городов осуществляется с помощью кнопок '<--назад' и 'вперёд-->'", reply_markup=middle_location_markup)
    return CHOOSING_CITY


def end_choosing_city(update: Update, _: CallbackContext) -> int:
    global page_counter
    print(page_counter)
    end_location_choice = [*location_triplets[-1], ['<--назад']]
    end_location_markup = ReplyKeyboardMarkup(end_location_choice, one_time_keyboard=True)
    update.message.reply_text("Навигация по списку городов осуществляется с помощью кнопок '<--назад' и 'вперёд-->'", reply_markup=end_location_markup)
    return CHOOSING_CITY


def inc_choosing_city(update: Update, context: CallbackContext):
    global page_counter
    page_counter += 1
    if page_counter != len(location_triplets)-1:
        return mid_choosing_city(update, context)
    return end_choosing_city(update, context)


def dec_choosing_city(update: Update, context: CallbackContext):
    global page_counter
    page_counter -= 1
    if page_counter != 0:
        return mid_choosing_city(update, context)
    return begin_choosing_city(update, context)


def city_choice_confirmed(update: Update, context: CallbackContext):
    user_data = context.user_data
    city = update.message.text
    if city in locations:
        user_data['location'] = city
        return choosing_category(update, context)
    update.message.reply_text(f'Пожалуйста попробуйте ещё раз! Выбирайте город только из тех, что представлены в меню ниже!')
    return begin_choosing_city(update, context)


def choosing_category(update: Update, _: CallbackContext) -> int:
    category_choice = [['Зооняня', 'Передержка'], ['Садик для животных'], ['Кинолог', 'Грумер'], ['Завершить работу Petplaces Bot']]
    category_markup = ReplyKeyboardMarkup(category_choice, one_time_keyboard=True)
    update.message.reply_text("""Отлично!\nPetplaces помогает найти именно ту помощь, которая необходима вам и вашему питомцу. На данный момент основные категории это:\n
- ЗООНЯНИ - люди, которые готовы прийти к вам в дом и покормить/выгулять питомца, но не готовы взять его к себе в дом\n- ПЕРЕДЕРЖКИ - люди, которые готовы разово разместить животное у себя дома на время вашего отезда\n- САДИКИ ДЛЯ ПИТОМЦЕВ - готовые ежедневно принимать одного или нескольких питомцев у себя дома на время работы хозяина (как детский сад - только для ваших питомцев!)\n
Также на нашем сервисе есть возможность получить услуги настоящих профессионалов:\n\n- КИНОЛОГОВ\n- ГРУМЕРОВ\n
Выберите нужную категорию, нажав на одну из кнопок ниже.""", reply_markup=category_markup)
    return CHOOSING_CATEGORY


def category_choice_confirmed(update: Update, context: CallbackContext):
    user_data = context.user_data
    category = update.message.text
    category_choice = [['Зооняня', 'Передержка'], ['Садик'], ['Кинолог', 'Грумер'], ['Завершить работу Petplaces Bot']]
    category_markup = ReplyKeyboardMarkup(category_choice, one_time_keyboard=True)
    if category in categories:
        user_data['category'] = category
        return all_params_chosen(update, context)
    update.message.reply_text(f'Пожалуйста попробуйте ещё раз! Выберите категорию только из тех, что представлены в меню ниже!', reply_markup=category_markup)
    return CHOOSING_CATEGORY


def all_params_chosen(update: Update, context: CallbackContext):
    fallback_choice = [['Завершить работу Petplaces Bot']]
    fallback_markup = ReplyKeyboardMarkup(fallback_choice, one_time_keyboard=True)
    user_data = context.user_data
    if find_suitable(pet_places_collection(), {'location': user_data['location'], 'category': user_data['category']}):
        update.message.reply_text(f'Отлично! Ниже приведён список тех, кто готов вам помочь', reply_markup=fallback_markup)
        for performer in find_suitable(pet_places_collection(), {'location': user_data['location'], 'category': user_data['category']}):
            performer_list = [f'{key} - {value}' for key, value in performer.items()]
            update.message.reply_text(f'{performer_list}')
    else:
        update.message.reply_text(f'К сожалению, на данный момент в вашем городе никто не может оказать такую услугу :(', reply_markup=fallback_markup)


def fallback(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text('Вы вышли из Petplaces Bot. Чтобы запустить его заново введите "/start".')
    return ConversationHandler.END


def main() -> None:
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={GREETINGS: [MessageHandler(Filters.regex('^Выбрать свой город$'), choosing_city),
                            MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Завершить работу Petplaces Bot$')), fallback)],
                CHOOSING_CITY: [MessageHandler(Filters.regex('^вперёд-->$'), inc_choosing_city),
                                MessageHandler(Filters.regex('^<--назад$'), dec_choosing_city),
                                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Завершить работу Petplaces Bot$')), city_choice_confirmed)],
                CHOOSING_CATEGORY: [MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Завершить работу Petplaces Bot$')), category_choice_confirmed)]},
        fallbacks=[MessageHandler(Filters.regex('^Завершить работу Petplaces Bot$'), fallback)])
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
