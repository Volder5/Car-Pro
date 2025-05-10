from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import Database
import keyboards as kb
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

router = Router()

class BudgetForm(StatesGroup):
    waiting_for_budget = State()

@router.callback_query(lambda c: c.data == "set_budget")
async def start_budget_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your budget (in numeric format, e.g., 100000):")
    await state.set_state(BudgetForm.waiting_for_budget)
    await callback.answer()

@router.message(BudgetForm.waiting_for_budget, F.text.regexp(r"^\d+$"))
async def process_budget(message: Message, state: FSMContext, db: Database):
    budget = int(message.text)
    db.update_user_budget(message.from_user.id, budget)
    await message.delete()  # Delete the user's input message
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,  # Previous bot message
        text=f"Budget set: {budget}.",
        reply_markup=kb.menus["params"]["keyboard"]
    )
    await state.clear()
    logging.debug(f"Budget {budget} set for user_id={message.from_user.id}")

@router.message(BudgetForm.waiting_for_budget)
async def process_invalid_budget(message: Message):
    await message.delete()  # Delete invalid input
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id - 1,
        text="Budget must be a number! Try again:"
    )