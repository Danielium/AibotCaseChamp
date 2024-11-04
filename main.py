import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from fal import process_images  # Импортируем функцию обработки изображений с нейросетью

os.environ["FAL_KEY"] = "0d4ed3c0-67bb-4bf4-8b36-1ca35973a266:6cc73bf649d3d4842f5a83a01bd7639a"
BOT_TOKEN = '7829353526:AAE3kK88AJD81DrIIdkx5sBpP_uAD3d7QRw'

start = 'Привет! Этот бот поможет вам определить, как будет выглядеть на вас выбранная одежда. Просто отправьте мне ' \
        'сначала фотографию одежды, а после этого фотографию вас.'

router = Router()


class Form(StatesGroup):
    clothes = State()
    photo = State()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(start.format(name=message.from_user.full_name))


@router.message(F.photo)
async def download_photo(message: Message, bot: Bot, state: FSMContext):
    # Получаем фотографию с наибольшим разрешением
    photo = message.photo[-1]

    # Проверяем текущее состояние FSM
    current_state = await state.get_state()

    if current_state is None or current_state == Form.clothes.state:  # Ожидаем фотографию одежды
        await bot.download(
            photo.file_id,
            destination=f"data/clothes_{photo.file_id}.jpg"  # Сохраняем с префиксом для одежды
        )
        await state.update_data(clothes=f"data/clothes_{photo.file_id}.jpg")
        await state.set_state(Form.photo)  # Устанавливаем состояние ожидания фото человека
        await message.reply("Вы отправили фотографию одежды! Теперь отправьте фотографию человека.")

    elif current_state == Form.photo.state:  # Ожидаем фотографию человека
        await bot.download(
            photo.file_id,
            destination=f"data/person_{photo.file_id}.jpg"  # Сохраняем с префиксом для человека
        )
        await state.update_data(photo=f"data/person_{photo.file_id}.jpg")

        await message.reply("Вы отправили фотографию человека! Обработка займет около минуты. Ожидайте...")

        # Вызываем функцию для загрузки изображений и обработки
        result_url = await process_images(state)  # Передаём состояние для обработки

        # Проверяем результат и отправляем сообщение пользователю
        if result_url:
            await message.reply(f"Вот результат: {result_url}")  # Отправляем ссылку на результат
        else:
            await message.reply("Произошла ошибка при обработке изображения.")

        await state.set_state(None)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        defaults={"parse_mode": ParseMode.HTML}
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
