import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Токен твоего бота
TOKEN = "8909626657:AAGhELdyS6RTpQDw5MpOxKEgDLzbHzsACmE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Предметы: IFP, COA и WEB
SUBJECTS = [
    "IFP", 
    "COA",
    "WEB"
]

# Словарь для хранения очередей: ключ — предмет, значение — список студентов
queues = {subject: [] for subject in SUBJECTS}

# Состояния FSM (для пошагового выбора)
class QueueStates(StatesGroup):
    choosing_subject_for_booking = State()
    choosing_subject_for_viewing = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для записи на дефенсы (IFP, COA, WEB).\n\n"
        "Доступные команды:\n"
        "/book — Записаться на дефенс\n"
        "/queue — Посмотреть очередь по предмету\n"
        "/leave — Отменить свою запись"
    )

# Шаг 1: Нажали /book — показываем выбор предметов кнопками
@dp.message(Command("book"))
async def cmd_book(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.row(types.InlineKeyboardButton(text=subject, callback_data=f"book_{subject}"))
    
    await message.answer("📚 Выбери предмет, по которому хочешь записаться на дефенс:", reply_markup=builder.as_markup())
    await state.set_state(QueueStates.choosing_subject_for_booking)

# Обработка выбора предмета для брони
@dp.callback_query(lambda c: c.data.startswith("book_"))
async def process_booking(callback: types.CallbackQuery, state: FSMContext):
    subject = callback.data.replace("book_", "")
    user_name = callback.from_user.full_name
    
    # Проверяем, записан ли уже студент на этот предмет
    already_booked = False
    for subj, students in queues.items():
        if user_name in students:
            already_booked = True
            break
            
    if already_booked:
        await callback.message.answer(f"⚠️ {user_name}, ты уже записан в очередь на один из предметов! Сначала выйди из текущей очереди через /leave.")
    else:
        queues[subject].append(user_name)
        position = len(queues[subject])
        await callback.message.answer(f"✅ Успешно! {user_name}, ты записан на дефенс по предмету **{subject}** под номером **{position}**.", parse_mode="Markdown")
    
    await callback.answer()
    await state.clear()

# Команда /queue — посмотреть очередь по предметам
@dp.message(Command("queue"))
async def cmd_queue(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.row(types.InlineKeyboardButton(text=subject, callback_data=f"view_{subject}"))
    
    await message.answer("📋 Выбери предмет, чтобы посмотреть текущую очередь:", reply_markup=builder.as_markup())
    await state.set_state(QueueStates.choosing_subject_for_viewing)

# Обработка выбора предмета для просмотра
@dp.callback_query(lambda c: c.data.startswith("view_"))
async def process_view_queue(callback: types.CallbackQuery, state: FSMContext):
    subject = callback.data.replace("view_", "")
    student_list = queues[subject]
    
    if not student_list:
        text = f"📭 Очередь на дефенс по предмету **{subject}** пока пуста."
    else:
        text = f"📋 **Очередь на дефенс ({subject}):**\n"
        for index, student in enumerate(student_list, start=1):
            text += f"{index}. {student}\n"
            
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()
    await state.clear()

# Команда /leave — отменить свою запись
@dp.message(Command("leave"))
async def cmd_leave(message: types.Message):
    user_name = message.from_user.full_name
    removed = False
    
    for subject in SUBJECTS:
        if user_name in queues[subject]:
            queues[subject].remove(user_name)
            removed = True
            await message.answer(f"❌ Ты успешно удален из очереди по предмету **{subject}**.", parse_mode="Markdown")
            break
            
    if not removed:
        await message.answer("Ты не найден ни в одной активной очереди.")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())