from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
import keyboards as kb
from database import Database
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    db.add_user(message.from_user.id)
    logging.debug(f"Sending main menu for user_id={message.from_user.id}")
    await message.answer("Hello, please select a suitable category:", reply_markup=kb.menus["main"]["keyboard"])

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    logging.debug(f"Sending main menu via /menu for user_id={message.from_user.id}")
    await message.answer(kb.menus["main"]["text"], reply_markup=kb.menus["main"]["keyboard"])

@router.message(Command("reset"))
async def reset_db(message: Message, db: Database):
    db.reset_sent_listings()
    await message.answer("The database of sent listings has been reset!")

@router.message(Command("help"))
async def get_help(message: Message):
    await message.answer("Command /help")