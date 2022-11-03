import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.handlers.meeting import register_meeting
from tgbot.handlers.groups import register_group
from tgbot.middlewares.environment import EnvironmentMiddleware


logger = logging.getLogger(__name__)
config = load_config(".env")

WEBHOOK_PATH = f"/bot/{config.tg_bot.token}"
WEBHOOK_URL = config.tg_bot.webhook_url + WEBHOOK_PATH


def register_all_middlewares(dp, config):
    dp.setup_middleware(EnvironmentMiddleware(config=config))


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)
    register_meeting(dp)


logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)
logger.info("Starting bot")
config = load_config(".env")

storage = RedisStorage2() if config.tg_bot.use_redis else MemoryStorage()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage, )
bot['config'] = config

print(bot['config'])

register_all_middlewares(dp, config)
register_all_filters(dp)
register_all_handlers(dp)
register_group(dp)


async def on_startup(dp):
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )