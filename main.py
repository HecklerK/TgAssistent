import logging
import logging.handlers
import re
from decouple import config
from pyrogram  import Client, filters
from pyrogram.types import Message, Chat

logging.basicConfig(level=logging.INFO, filename="logs.txt", filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.handlers.RotatingFileHandler("logs.txt", maxBytes=2048, backupCount=2)

logging.info("Start!")

bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'))

async def isNotFakeScam(client: Client, message: Message):
    user = message.from_user
    if (user.is_fake | user.is_scam):
        await client.send_message(chat_id="me", text=f"Пользователь {user.username} помечен как фейк/скам")
        return False
    
    return True


@bot.on_message(filters.text & (filters.private | filters.chat("me")))
async def handle_message(client: Client, message: Message):
    text = message.text.lower()

    if (text == '\U00002754') & await isNotFakeScam(client, message):
        answer = await message.reply(text=config('ABOUT_ME'), quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    elif (re.search(r'расскажи о себе|расскажешь о себе', text) != None) & (not message.from_user.is_self) & await isNotFakeScam(client, message):
        answer = await message.reply(chat_id=message.chat.id, text=('Автоматическое сообщение: ' + config('ABOUT_ME')), quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    
    if message.from_user.is_self & ("\U00002754 " in text):
        user_id = text.split("\U00002754 ")[1].strip()
        user = await client.get_users(user_id)

        if user != None:
            flags = ''
            if user.is_scam:
                flags += "Скам"
            if user.is_fake:
                flags += "Фейк"
            if user.is_premium:
                flags += "Премиум"
            if user.is_verified:
                flags += "Верифицирован"
            if user.is_support:
                flags += "Telegram support"

            last_online = ''
            if user.last_online_date != None:
                user.last_online_date != None

            await message.reply(text=f'Пользователь {user.username},\nИмя {user.first_name},\nФамилия {user.last_name},\nМетки {flags},\nКод страны {user.language_code},\nПоследняя дата в сети {last_online}', quote=True)


bot.run()