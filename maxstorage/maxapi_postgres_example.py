"""
Пример использования PostgresStorage для maxapi бота.

Этот пример показывает, как настроить персистентное хранилище PostgreSQL
для FSM-бота на maxapi вместо использования MemoryContext.
"""

import asyncio
from maxapi import Bot, F
from maxapi.types import MessageCreated
from maxapi.context import StatesGroup, State

# Импортируем наш PostgreSQL storage и dispatcher
import sys
sys.path.append('..')
from modules.maxstorage import PostgresStorage, PostgresDispatcher


# Определяем состояния FSM
class UserForm(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_city = State()


# Инициализация бота
bot = Bot(token="YOUR_MAX_TOKEN")

# Инициализируем PostgreSQL storage
storage = PostgresStorage(
    host='localhost',
    port=5432,
    database='maxapi_fsm',
    user='bot',
    password='password'
)

# Создаём диспетчер с PostgreSQL storage
dp = PostgresDispatcher(storage=storage)


# Обработчик команды /start
@dp.message_created(F.message.body.text == '/start')
async def cmd_start(event: MessageCreated, context):
    """Начало диалога с пользователем"""
    await event.message.answer(
        "Привет! Давайте познакомимся.\n"
        "Как вас зовут?"
    )
    await context.set_state(UserForm.waiting_name)


# Обработчик получения имени
@dp.message_created(F.message.body.text, state=UserForm.waiting_name)
async def process_name(event: MessageCreated, context):
    """Сохраняем имя и спрашиваем возраст"""
    await context.update_data(name=event.message.body.text)
    await event.message.answer(f"Приятно познакомиться, {event.message.body.text}!\nСколько вам лет?")
    await context.set_state(UserForm.waiting_age)


# Обработчик получения возраста
@dp.message_created(F.message.body.text, state=UserForm.waiting_age)
async def process_age(event: MessageCreated, context):
    """Сохраняем возраст и спрашиваем город"""
    if not event.message.body.text.isdigit():
        await event.message.answer("Пожалуйста, введите число.")
        return
    
    await context.update_data(age=int(event.message.body.text))
    await event.message.answer("Из какого вы города?")
    await context.set_state(UserForm.waiting_city)


# Обработчик получения города
@dp.message_created(F.message.body.text, state=UserForm.waiting_city)
async def process_city(event: MessageCreated, context):
    """Сохраняем город и выводим всю информацию"""
    await context.update_data(city=event.message.body.text)
    
    # Получаем все сохранённые данные
    data = await context.get_data()
    
    await event.message.answer(
        f"Отлично! Вот ваши данные:\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Город: {data['city']}\n\n"
        f"Эти данные сохранены в PostgreSQL и не потеряются при перезагрузке бота!\n"
        f"Отправьте /reset чтобы очистить данные или /show чтобы показать их снова."
    )
    await context.clear()


# Обработчик команды /show
@dp.message_created(F.message.body.text == '/show')
async def cmd_show(event: MessageCreated, context):
    """Показывает сохранённые данные"""
    data = await context.get_data()
    
    if not data:
        await event.message.answer("У вас нет сохранённых данных. Используйте /start для начала.")
        return
    
    await event.message.answer(
        f"Ваши сохранённые данные:\n"
        f"Имя: {data.get('name', 'не указано')}\n"
        f"Возраст: {data.get('age', 'не указан')}\n"
        f"Город: {data.get('city', 'не указан')}"
    )


# Обработчик команды /reset
@dp.message_created(F.message.body.text == '/reset')
async def cmd_reset(event: MessageCreated, context):
    """Очищает все данные и состояние"""
    await context.clear()
    await event.message.answer("Все данные очищены. Используйте /start для начала.")


# Обработчик для всех остальных сообщений
@dp.message_created(F.message.body.text)
async def echo_handler(event: MessageCreated, context):
    """Эхо-обработчик вне FSM"""
    data = await context.get_data()
    state = await context.get_state()
    
    await event.message.answer(
        f"Вы написали: {event.message.body.text}\n"
        f"Текущее состояние: {state}\n"
        f"Сохранённые данные: {data}\n\n"
        f"Используйте /start для начала диалога."
    )


async def main():
    """Главная функция запуска бота"""
    try:
        # ВАЖНО: Инициализируем storage и создаём таблицы
        await storage.init()
        print("PostgreSQL storage инициализирован")
        
        # PostgresDispatcher уже настроен на использование PostgreSQL
        # Каждый пользователь будет автоматически получать свой PostgresContext
        
        print("Бот запущен с PostgreSQL хранилищем")
        await dp.start_polling(bot)
        
    finally:
        # Закрываем соединение с базой при остановке бота
        await storage.close()
        print("Соединение с PostgreSQL закрыто")


if __name__ == "__main__":
    asyncio.run(main())
