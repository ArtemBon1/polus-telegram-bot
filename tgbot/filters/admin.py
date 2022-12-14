import typing

from aiogram.dispatcher.filters import BoundFilter
from aiogram.utils.callback_data import CallbackData

from tgbot.config import Config

admin_action_callback = CallbackData("admin", "action", "value")
admin_back_callback = CallbackData("admin_back", "location", "value")


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin

    async def check(self, obj):
        if self.is_admin is None:
            return False
        config: Config = obj.bot.get('config')
        return (obj.from_user.id in config.tg_bot.admin_ids) == self.is_admin

