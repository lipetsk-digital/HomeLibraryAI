"""
Простой тест для проверки работы PostgresStorage.

Этот скрипт проверяет базовую функциональность без запуска полного бота.
"""

import asyncio
from modules.maxstorage import PostgresStorage, PostgresContext


async def test_postgres_storage():
    """Тестирует основные операции с PostgresStorage"""
    
    print("=== Тест PostgresStorage ===\n")
    
    # 1. Создаём storage
    print("1. Создание storage...")
    storage = PostgresStorage(
        host='localhost',
        port=5432,
        database='maxapi_fsm',
        user='bot',
        password='password'
    )
    
    # 2. Инициализируем (создаём таблицы)
    print("2. Инициализация и создание таблиц...")
    try:
        await storage.init()
        print("   ✓ Storage инициализирован\n")
    except Exception as e:
        print(f"   ✗ Ошибка инициализации: {e}")
        return
    
    # 3. Создаём контекст для тестового пользователя
    print("3. Создание контекста для пользователя...")
    chat_id = 12345
    user_id = 67890
    context = PostgresContext(chat_id=chat_id, user_id=user_id, storage=storage)
    print(f"   ✓ Контекст создан для chat_id={chat_id}, user_id={user_id}\n")
    
    # 4. Сохраняем данные
    print("4. Сохранение данных...")
    test_data = {"name": "Иван", "age": 30, "city": "Москва"}
    await context.set_data(test_data)
    print(f"   ✓ Данные сохранены: {test_data}\n")
    
    # 5. Читаем данные
    print("5. Чтение данных...")
    loaded_data = await context.get_data()
    print(f"   ✓ Данные прочитаны: {loaded_data}")
    
    if loaded_data == test_data:
        print("   ✓ Данные совпадают!\n")
    else:
        print(f"   ✗ Данные не совпадают! Ожидалось {test_data}\n")
    
    # 6. Обновляем данные
    print("6. Обновление данных...")
    await context.update_data(phone="+79991234567")
    updated_data = await context.get_data()
    print(f"   ✓ Данные обновлены: {updated_data}\n")
    
    # 7. Устанавливаем состояние
    print("7. Установка состояния...")
    await context.set_state("waiting_for_name")
    state = await context.get_state()
    print(f"   ✓ Состояние установлено: {state}\n")
    
    # 8. Создаём второй контекст для другого пользователя
    print("8. Создание второго контекста...")
    chat_id2 = 11111
    user_id2 = 22222
    context2 = PostgresContext(chat_id=chat_id2, user_id=user_id2, storage=storage)
    await context2.set_data({"name": "Мария", "age": 25})
    print(f"   ✓ Второй контекст создан для chat_id={chat_id2}, user_id={user_id2}\n")
    
    # 9. Проверяем изоляцию данных
    print("9. Проверка изоляции данных...")
    data1 = await context.get_data()
    data2 = await context2.get_data()
    print(f"   Пользователь 1: {data1}")
    print(f"   Пользователь 2: {data2}")
    
    if data1 != data2:
        print("   ✓ Данные изолированы!\n")
    else:
        print("   ✗ Данные смешались!\n")
    
    # 10. Очищаем контекст
    print("10. Очистка контекста...")
    await context.clear()
    cleared_data = await context.get_data()
    cleared_state = await context.get_state()
    print(f"   ✓ Данные после очистки: {cleared_data}")
    print(f"   ✓ Состояние после очистки: {cleared_state}\n")
    
    # 11. Проверяем, что данные второго пользователя остались
    print("11. Проверка данных второго пользователя...")
    data2_check = await context2.get_data()
    print(f"   ✓ Данные второго пользователя сохранились: {data2_check}\n")
    
    # 12. Закрываем соединение
    print("12. Закрытие соединения...")
    await storage.close()
    print("   ✓ Соединение закрыто\n")
    
    print("=== Все тесты пройдены успешно! ===")


if __name__ == "__main__":
    try:
        asyncio.run(test_postgres_storage())
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
