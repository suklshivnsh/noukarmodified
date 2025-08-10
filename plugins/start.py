# © @TheAlphaBotz for this code 
# @TheAlphaBotz [2021-2025]
# © Utkarsh dubey [github.com/utkarshdubey2008]
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest, ChatMemberUpdated
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserBannedInChannel

from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, 
    PROTECT_CONTENT, START_PIC, AUTO_DELETE_TIME, AUTO_DELETE_MSG, 
    JOIN_REQUEST_ENABLE, FORCE_SUB_CHANNEL, HEAVY_LOAD_MSG, OWNER_ID
)
from helper_func import (
    subscribed, decode, process_file_request, delete_file
)
from database.database import add_user, del_user, full_userbase, present_user, add_join_request, check_join_request_exists, remove_join_request
from datetime import datetime

async def is_user_authorized(client: Client, user_id: int):
    if not FORCE_SUB_CHANNEL or not JOIN_REQUEST_ENABLE:
        return True
    
    if await check_join_request_exists(FORCE_SUB_CHANNEL, user_id):
        return True
    
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
    except:
        pass
    
    return False

@Bot.on_chat_join_request()
async def handle_join_request(client, chat_join_request: ChatJoinRequest):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id
    
    if chat_id == FORCE_SUB_CHANNEL:
        await add_join_request(chat_id, user_id)

@Bot.on_chat_member_updated()
async def handle_member_updates(client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id
    
    if chat_id == FORCE_SUB_CHANNEL:
        old_member = chat_member_updated.old_chat_member
        if old_member and old_member.status == ChatMemberStatus.MEMBER:
            user_id = old_member.user.id
            await remove_join_request(chat_id, user_id)

async def send_media_and_reply(client, message, messages, temp_msg=None):
    track_msgs = []
    
    for msg in messages:
        if not msg:
            continue
            
        try:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html, 
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None
                
            if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                if copied_msg:
                    track_msgs.append(copied_msg)
            else:
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
            
            await asyncio.sleep(0.7)
            
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                if copied_msg:
                    track_msgs.append(copied_msg)
            else:
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
        except Exception as e:
            print(f"Error sending message: {e}")
    
    if track_msgs and AUTO_DELETE_TIME > 0:
        delete_data = await message.reply_text(AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME))
        asyncio.create_task(delete_file(track_msgs, client, delete_data))
    
    if temp_msg:
        try:
            await temp_msg.delete()
        except:
            pass

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    
    text = message.text
    
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            await process_file_request(client, message, string)
            return
        except Exception as e:
            await message.reply_text("Invalid link or format. Please use a valid file link.", quote=True)
            print(f"Error decoding start command: {e}")
            return
    
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😊 About Me", callback_data="about"),
                InlineKeyboardButton("🔒 Close", callback_data="close")
            ]
        ]
    )
    
    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            quote=True
        )
    else:
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    id = message.from_user.id
    
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    
    if id in ADMINS or await is_user_authorized(client, id):
        return await start_command(client, message)
    
    if bool(JOIN_REQUEST_ENABLE):
        try:
            invite_link = await client.create_chat_invite_link(
                chat_id=FORCE_SUB_CHANNEL,
                creates_join_request=True
            )
            ButtonUrl = invite_link.invite_link
        except Exception as e:
            print(f"Error creating join request link: {e}")
            try:
                chat = await client.get_chat(FORCE_SUB_CHANNEL)
                ButtonUrl = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(FORCE_SUB_CHANNEL)[4:]}"
            except:
                ButtonUrl = f"https://t.me/c/{str(FORCE_SUB_CHANNEL)[4:]}"
    else:
        ButtonUrl = client.invitelink

    buttons = [
        [
            InlineKeyboardButton(
                "📝 Send Join Request" if JOIN_REQUEST_ENABLE else "Join Channel",
                url = ButtonUrl)
        ]
    ]
    
    if JOIN_REQUEST_ENABLE:
        buttons.append([
            InlineKeyboardButton("✅ Check Authorization", callback_data="check_auth")
        ])

    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_callback_query(filters.regex("check_auth"))
async def check_authorization(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await is_user_authorized(client, user_id):
        await callback_query.edit_message_text("✅ Authorized! You can now use the bot.")
    else:
        await callback_query.answer("❌ Send join request first!", show_alert=True)

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="Counting users...")
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(OWNER_ID))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        start_time = datetime.now()
        
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await broadcast_msg.copy(chat_id)
                    successful += 1
                except:
                    unsuccessful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Error broadcasting to {chat_id}: {e}")
                unsuccessful += 1
            total += 1
            
            if total % 50 == 0:
                progress = f"""<b>Broadcast Progress 📊</b>
                
<b>Total Users:</b> {len(query)}
<b>Completed:</b> {total} / {len(query)} (<code>{total/len(query)*100:.1f}%</code>)
<b>Success:</b> {successful}
<b>Failed:</b> {unsuccessful + blocked + deleted}

<i>Please wait, broadcasting in progress...</i>"""
                await pls_wait.edit(progress)
        
        time_taken = datetime.now() - start_time
        
        status = f"""<b>✅ Broadcast Completed</b>

<b>📊 Statistics:</b>
• <b>Total Users:</b> <code>{total}</code>
• <b>Successful:</b> <code>{successful}</code> (<code>{successful/total*100:.1f}%</code>)
• <b>Blocked Users:</b> <code>{blocked}</code>
• <b>Deleted Accounts:</b> <code>{deleted}</code>
• <b>Failed Delivery:</b> <code>{unsuccessful}</code>

<b>⏱ Time Taken:</b> <code>{time_taken.seconds}</code> seconds

<i>Note: Blocked and deleted users have been removed from the database</i>"""
        
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("❌ Please reply to a message to broadcast it to users.")
        await asyncio.sleep(5)
        await msg.delete()
