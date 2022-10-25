import asyncio

from aiogram import Bot

from datetime import datetime

from tgbot.models.db import Database
from tgbot.config import load_config
from tgbot.keyboards.inline import meeting_checkin


async def meeting_notification():

    config = load_config(".env")

    db = Database()
    db.create()

    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

    while True:
        for meeting_doc in db.getDocs(database='polus',
                                collection='meetings',
                                search={
                                    "status": True
                                }):
            meeting_date = meeting_doc['date']
            meeting_time = {
                'hour': int(meeting_doc['time'].split(":")[0]),
                'minute': int(meeting_doc['time'].split(":")[1].split(" ")[0])
            }
            current_date = datetime.now()
            if meeting_date.year == current_date.year and \
                    meeting_date.month == current_date.month and \
                    meeting_date.day == current_date.day and \
                    meeting_time.get('hour') == current_date.hour and \
                    meeting_time.get('minute') == current_date.minute and not \
                    'notified' in meeting_doc.keys():

                members = []

                for member in db.getDocs(database='polus', collection='user',
                                         search={"telegram_id": {"$in": meeting_doc['members']}}):
                    members.append(
                        f'@{member["username"]} ' + (
                            '✅' if member['telegram_id'] in meeting_doc['checkin'] else (
                                '❌' if member['telegram_id'] in meeting_doc['absent'].keys() else '➖'
                            )
                        )
                    )

                    remind_msg = f'❗️ {member["name"]}, скоро состоится мит с вашим участием, <strong>не</strong> забудьте прийти!\n\n' \
                                 f'📄 Мит: {meeting_doc["name"]}\n\n' \
                                 f'📈 Цель: {meeting_doc["goal"]}\n\n' \
                                 f'📆 Дата: {meeting_doc["date"].strftime("%d/%m/%Y")}\n' \
                                 f'⏰ Время: {meeting_doc["time"]}\n\n'
                    try:
                        await bot.send_message(chat_id=member['telegram_id'],
                                               text=remind_msg)
                    except(Exception) as e:
                        print(member, e)

                members = "\n".join(members)

                meeting = f'📄 Name: {meeting_doc["name"]}\n\n' \
                          f'📈 Object: {meeting_doc["goal"]}\n\n' \
                          f'📆 Date: {meeting_doc["date"].strftime("%d/%m/%Y")}\n' \
                          f'⏰ Time: {meeting_doc["time"]}\n\n' \
                          f'👥 Members: \n{members}'

                msg = await bot.send_message(chat_id=config.tg_bot.test_chat,
                                             text=meeting,
                                             reply_markup=meeting_checkin(meeting_doc))

                meeting_doc['pinned_msg_id'] = msg.message_id
                meeting_doc['notified'] = True
                db.updateDoc(database='polus',
                             collection='meetings',
                             search={'_id': meeting_doc['_id']},
                             update_doc=meeting_doc)

                await bot.pin_chat_message(chat_id=config.tg_bot.test_chat,
                                           message_id=msg.message_id)


if __name__ == '__main__':
    asyncio.run(meeting_notification())