import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import db
from utils import log
import handlers


async def main() -> None:
    pool = await db.connect_db()
    await db.postgres_version(pool)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["pool"] = pool

    async def on_startup() -> None:
        log.info("Bot start")

    async def on_shutdown() -> None:
        await dp.storage.close()
        await dp["pool"].close()
        await bot.session.close()
        log.info("Bot finish")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Регаем мидлваеры
    dp.message.middleware(handlers.middleware.DBMiddleware(dp["pool"]))

    # Регам роуторы


    await dp.start_polling(bot, handle_as_tasks=False)


if __name__ == "__main__":
    asyncio.run(main())