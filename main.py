import asyncio
from aiogram import Bot, Dispatcher
import logging
from config import TOKEN, DATABASE_PATH
from handlers import routers
from database import Database
from scheduler import setup_scheduler

bot = Bot(token=TOKEN)
from aiogram.fsm.storage.memory import MemoryStorage
dp = Dispatcher(storage=MemoryStorage())
db = Database(DATABASE_PATH)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        for router in routers:
            dp.include_router(router)
        scheduler = setup_scheduler(bot, db)
        scheduler.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, db=db)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    finally:
        db.close()