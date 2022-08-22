from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from bson import ObjectId

from tgbot.filters.user import start_join_callback
from tgbot.filters.admin import admin_action_callback
from tgbot.models.db import Database
from tgbot.states.admin import MeetingStatesGroup
import tgbot.keyboards as keyboards

from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar

db = Database()
db.create()

vote_cb = CallbackData('vote', 'action', 'value')  # post:<action>:<amount>


async def admin_start(message: Message):
    print(message)
    await message.reply("Hello, admin!")

async def admin_meeting_notify_list(message: Message):
    meetings_list = db.getDocs(database='polus', collection='meetings', search={"status": True})
    meetings = "📅 <strong>БЛИЖАЙШИЕ ТИМ МИТЫ POLUS</strong> 📅\n\n"

    for meeting in meetings_list:

        members = []
        for member in db.getDocs(database='polus', collection='user',
                                 search={"telegram_id": {"$in": meeting['members']}}):
            members.append(f'@{member["username"]}')
        members = "\n".join(members)

        meetings += f'📄 Name: {meeting["name"]}\n\n' \
                    f'📈 Object: {meeting["goal"]}\n\n' \
                    f'📆 Date: {meeting["date"].strftime("%d/%m/%Y")}\n' \
                    f'⏰ Time: {meeting["time"]}\n\n' \
                    f'👥 Members: \n{members}\n' \
                    f'------------------------------\n\n'
    await message.reply(meetings, reply_markup=keyboards.inline.meeting_notify(meetings_list))

async def admin_notify_group(callback_query: CallbackQuery, callback_data: dict):
    meeting_doc = db.getDoc(database='polus',
                            collection='meetings',
                            search={
                                "status": True,
                                '_id': ObjectId(callback_data.get('value'))
                            })

    members = []
    for member in db.getDocs(database='polus', collection='user',
                             search={"telegram_id": {"$in": meeting_doc['members']}}):
        members.append(f'@{member["username"]}')

        remind_msg = f'❗️ {member["name"]}, скоро состоится мит с вашим участием, забудьте прийти!\n\n' \
                     f'📄 Мит: {meeting_doc["name"]}\n\n' \
                     f'📈 Цель: {meeting_doc["goal"]}\n\n' \
                     f'📆 Дата: {meeting_doc["date"].strftime("%d/%m/%Y")}\n' \
                     f'⏰ Время: {meeting_doc["time"]}\n\n'
        try:
            await callback_query.bot.send_message(chat_id=member['telegram_id'],
                                                  text=remind_msg,
                                                  reply_markup=keyboards.inline.meeting_checkin_pm(meeting_doc))
        except(Exception) as e:
            print(member, e)

    members = "\n".join(members)

    meeting = f'📄 Name: {meeting_doc["name"]}\n\n' \
              f'📈 Object: {meeting_doc["goal"]}\n\n' \
              f'📆 Date: {meeting_doc["date"].strftime("%d/%m/%Y")}\n' \
              f'⏰ Time: {meeting_doc["time"]}\n\n' \
              f'👥 Members: \n{members}\n\n' \
              f'✅ Checkin\n'

    msg = await callback_query.bot.send_message(chat_id=callback_query.bot['config'].tg_bot.dev_chat,
                                                text=meeting,
                                                reply_markup=keyboards.inline.meeting_checkin(meeting_doc))
    await callback_query.bot.pin_chat_message(chat_id=callback_query.bot['config'].tg_bot.dev_chat,
                                              message_id=msg.message_id)


async def admin_add_meeting(message: Message):
    await MeetingStatesGroup.name.set()
    await message.answer('✏️ Enter name of meeting')


async def admin_meeting_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        await MeetingStatesGroup.date.set()
        data['message'] = await message.answer(
            text='📆 Select date of meeting',
            reply_markup=await SimpleCalendar().start_calendar()
        )

async def admin_meeting_time(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text
        await MeetingStatesGroup.goal.set()
        await data['message'].edit_text(
            f'📄 Name: {data["name"]}\n\n'
            f'📆 Date: {data["date"]}\n'
            f'⏰ Time: {message.text}\n\n'
            f'✏️ Whats the object of meeting?'
        )

async def admin_meeting_goal(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['goal'] = message.text
        await MeetingStatesGroup.member.set()
        await data['message'].edit_text(
            f'📄 Name: {data["name"]}\n\n'
            f'📈 Object: {data["goal"]}\n\n'
            f'📆 Date: {data["date"]}\n'
            f'⏰ Time: {data["time"]}\n\n'
            f'👥 Choose members'
        )
        await data['message'].edit_reply_markup(
            keyboards.inline.meeting_members(
                db.getDocs(database='polus', collection='user', search={})
            )
        )
        meeting_doc = {
            "creator": str(message.from_user.id),
            "name": data['name'],
            "goal": data['goal'],
            "date": data['date'],
            "time": data['time'],
            "status": True,
            "members": [],
            "checkin": [],
            "absent": {}
        }
        data['id'] = db.addDoc(database='polus', collection='meetings', document=meeting_doc)

async def admin_meeting_member(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback_query.data != '0':
            meeting_doc = db.getDoc(database='polus', collection='meetings', search={'_id': data['id']})
            meeting_doc['members'].append(callback_query.data)
            db.updateDoc(database='polus', collection='meetings', search={'_id': data['id']}, update_doc=meeting_doc)

            members = []
            for member in db.getDocs(database='polus', collection='user',
                                     search={"telegram_id": {"$in": meeting_doc['members']}}):
                members.append(f'@{member["username"]}')
            members = "\n".join(members)

            await data['message'].edit_text(
                f'📄 Name: {data["name"]}\n\n'
                f'📈 Object: {data["goal"]}\n\n'
                f'📆 Date: {data["date"]}\n'
                f'⏰ Time: {data["time"]}\n\n'
                f'👥 Members: {members}'
            )
            await data['message'].edit_reply_markup(
                keyboards.inline.meeting_members(
                    db.getDocs(database='polus', collection='user', search={
                        "telegram_id": {"$nin": meeting_doc['members']}
                    })
                )
            )
        else:
            await state.finish()
            await data['message'].edit_reply_markup(keyboards.inline.remove_keyboard())

async def admin_org_join_request(callback_query: CallbackQuery, callback_data: dict):
    user_doc = db.getDoc(database='polus', collection='user', search={'telegram_id': callback_data.get("user")})
    user_doc['status'] = 'member'
    try:
        if callback_data.get("action") == "accept":
            db.updateDoc(database='polus', collection='user', search={'_id': user_doc['_id']}, update_doc=user_doc)
            await callback_query.message.edit_text(f'@{user_doc["username"]} was accepted to organization!')
            await callback_query.bot.send_message(f'✅ Ваш запрос в организацию Polus принят!')
        else:
            await callback_query.message.edit_text(f'@{user_doc["username"]} was rejected to join organization!')
            await callback_query.bot.send_message(f'❌ Ваш запрос в организацию Polus отклонен!')
        await callback_query.message.edit_reply_markup(keyboards.inline.remove_keyboard())
    except(Exception) as e:
        print(e)


async def process_admin_calendar(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await MeetingStatesGroup.time.set()
        async with state.proxy() as data:
            data['date'] = date
            await data['message'].edit_text(
                f'📄 Name: {data["name"]}\n\n'
                f'📆 Date: {date.strftime("%d/%m/%Y")}\n\n'
                f'✏️ Enter time of meeting'
            )


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
    dp.register_message_handler(admin_meeting_notify_list, commands=["meetings"], is_admin=True)
    #dp.register_message_handler(admin_migrate_db, commands=['migrate'], is_admin=True)
    dp.register_message_handler(admin_add_meeting, commands=['add_meeting'], is_admin=True)
    dp.register_message_handler(admin_meeting_name, state=MeetingStatesGroup.name, is_admin=True)
    dp.register_message_handler(admin_meeting_time, state=MeetingStatesGroup.time, is_admin=True)
    dp.register_message_handler(admin_meeting_goal, state=MeetingStatesGroup.goal, is_admin=True)
    dp.register_callback_query_handler(admin_notify_group, admin_action_callback.filter(action="notify_group"), is_admin=True)
    dp.register_callback_query_handler(admin_org_join_request, start_join_callback.filter(), is_admin=True)
    dp.register_callback_query_handler(admin_meeting_member, state=MeetingStatesGroup.member, is_admin=True)
    dp.register_callback_query_handler(process_admin_calendar, simple_cal_callback.filter(),
                                       state=MeetingStatesGroup.date,
                                       is_admin=True)
    #dp.register_message_handler(admin_test, commands=['test'], is_admin=True)

