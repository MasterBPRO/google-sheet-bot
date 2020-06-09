import src
import sheet
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

bot = Bot(token=src.token)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

logging.basicConfig(level=logging.INFO)

# Кнопка для старта Регистации
main_key = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
main_key.add(src.startKey)

# Клавиатура для удаления клавиатуры
removeKey = types.ReplyKeyboardRemove()

# Кнопка для получения номера телефона
getPhoneKey = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
getPhoneKeyButton = types.KeyboardButton(text="Поделитья номером телефона", request_contact=True)
getPhoneKey.add(getPhoneKeyButton)

# Доступные вакансии
actualWork_key = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
actualWork_key.add("Директор")
actualWork_key.add("Уборщица")
actualWork_key.add("Охрана")
actualWork_key.add("Бухгалтер")
actualWork_key.add("Кассир")

# Словарь в котором будут храниться данные введеные пользователями
data = {123456789: {}}


# Класс для Конечный автоматов
class FSMSet(StatesGroup):
    waitName = State()
    waitYear = State()
    checkAge = State()
    waitVacancy = State()
    waitExperience = State()
    waitPhone = State()


@dp.message_handler(commands=['start', 'restart'], state="*")
async def start_com(message, state: FSMContext):
    await state.finish()  # Чистим конечные автоматы

    data[message.chat.id] = {'name': '',
                             'year': '',
                             'job': '',
                             'experience': '',
                             'phone': '', }

    await message.answer(text=src.startCom.format(message.from_user.first_name),
                         reply_markup=main_key,
                         parse_mode="html")


@dp.message_handler(commands=['help'])
async def help_com(message):
    await message.answer(text=src.helpCom,
                         reply_markup=None,
                         parse_mode='html')


@dp.message_handler(text=src.startKey)
async def reg_com(message):
    await message.answer(text=src.getName)
    await FSMSet.waitName.set()


@dp.message_handler(state=FSMSet.waitName, content_types=types.ContentTypes.TEXT)
async def getAge(message):
    """
    Функция для получения возраста пользователя
    :param message:
    :return:
    """
    try:
        data[message.chat.id]['name'] = message.text  # Занесения имени в словарь

        await message.answer(text=src.getAge,
                             reply_markup=None,
                             parse_mode='html')

        await FSMSet.waitYear.set()

    except KeyError:
        await message.answer(text=src.userError,
                             parse_mode="html")


@dp.message_handler(state=FSMSet.waitYear, content_types=types.ContentTypes.TEXT)
async def getJob(message: types.Message, state: FSMContext):
    """
    Функция для выбора желаемой работы
    :param state:
    :param message:
    :return:
    """
    try:
        if int(message.text) < 18:
            await message.answer(src.yearError)
            await state.finish()

        else:
            data[message.chat.id]['year'] = message.text  # Занесения возраста в словрь

            await message.answer(text=src.getJob,
                                 reply_markup=actualWork_key,
                                 parse_mode='html')

            await FSMSet.waitVacancy.set()

    except ValueError:
        await FSMSet.waitYear.set()
        await message.answer(text=src.intAgeError,
                             parse_mode="html")
    except KeyError:
        await message.answer(text=src.userError,
                             parse_mode="html")


@dp.message_handler(state=FSMSet.waitVacancy, content_types=types.ContentTypes.TEXT)
async def getExperience(message):
    """
    Функция для получения опыта работы
    :param message:
    :return:
    """
    try:
        data[message.chat.id]['job'] = message.text  # Занесения желаемой работы в словарь

        await message.answer(text=src.getExperience,
                             reply_markup=None,
                             parse_mode='html')

        await FSMSet.waitExperience.set()

    except KeyError:
        await message.answer(text=src.userError,
                             parse_mode="html")


@dp.message_handler(state=FSMSet.waitExperience, content_types=types.ContentTypes.TEXT)
async def getPhone(message, loop=False):
    """
    Функция для получения номера телефона пользователя
    :param loop:
    :param message:
    :return:
    """
    try:
        if not loop:
            data[message.chat.id]['experience'] = message.text  # Занесения опыта в словарь

        await message.answer(text=src.getPhone,
                             reply_markup=getPhoneKey,
                             parse_mode='html')

        await FSMSet.waitPhone.set()
    except KeyError:
        await message.answer(text=src.userError,
                             parse_mode="html")


@dp.message_handler(state=FSMSet.waitPhone, content_types=types.ContentTypes.ANY)
async def checkPhone(message: types.Message, state: FSMContext):
    """
    Фунция для проверки номера телефона пользователя по заданному шаблону
    :param state:
    :param message:
    :return:
    """
    try:
        chat_id = message.chat.id
        username = message.from_user.username
        name = data[chat_id]['name']
        year = data[chat_id]['year']
        vacancy = data[chat_id]['job']
        experience = data[chat_id]['experience']

        if message.contact is not None:
            number = message.contact.phone_number
        else:
            number = message.text

        if str(number).startswith('+380') or str(number).startswith('380') and len(number) > 10:
            print(data)
            status = sheet.writeTable(chat_id, username, name, year, vacancy, experience, number)

            if status:
                await message.answer(text=src.goodLuck.format(message.from_user.first_name),
                                     parse_mode='html',
                                     reply_markup=main_key)
                await state.finish()

        else:
            await message.answer(text=src.getPhoneError)
            await getPhone(message, loop=True)  # Обратно к функции для запроса номера телефона

    except KeyError:
        await message.answer(text=src.userError,
                             parse_mode="html")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
