from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    mongo: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool
    dev_chat: str
    test_chat: str


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
            dev_chat=env.str("DEV_CHAT_ID"),
            test_chat=env.str("TEST_CHAT_ID")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME'),
            mongo=env.str('MONGO_CONNECTION_STRING')
        ),
        misc=Miscellaneous()
    )
