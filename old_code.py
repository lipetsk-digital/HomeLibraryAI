# Обработчик команды /start
@dp.message(Command("start"))
async def command_start(message: types.Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        # Проверяем существование пользователя
        user_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)",
            message.from_user.id
        )
        
        if not user_exists:
            await conn.execute(
                "INSERT INTO users (user_id) VALUES ($1)",
                message.from_user.id
            )

    await message.answer("Привет! Давай познакомимся. Как тебя зовут?")
    await state.set_state(Form.first_name)

# Обработчик для имени
@dp.message(Form.first_name)
async def process_first_name(message: types.Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET first_name = $1 WHERE user_id = $2",
            message.text, message.from_user.id
        )
    
    await state.update_data(first_name=message.text)
    await message.answer("Отлично! Теперь введи свою фамилию:")
    await state.set_state(Form.last_name)

# Обработчик для фамилии
@dp.message(Form.last_name)
async def process_last_name(message: types.Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_name = $1 WHERE user_id = $2",
            message.text, message.from_user.id
        )
    
    await state.update_data(last_name=message.text)
    await message.answer("Теперь укажи свою должность:")
    await state.set_state(Form.position)

# Обработчик для должности
@dp.message(Form.position)
async def process_position(message: types.Message, state: FSMContext, pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET position = $1 WHERE user_id = $2",
            message.text, message.from_user.id
        )
    
    user_data = await state.get_data()
    await message.answer(
        f"Приветствую, {user_data['first_name']} {user_data['last_name']}!\n"
        f"Твоя должность: {message.text}\n"
        "Рад знакомству!"
    )
    await state.clear()
