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
        await client.send_message(chat_id=message.chat.id, text="Вы помечены как фейк/скам")
        return False
    
    return True


@bot.on_message(filters.text & (filters.private | filters.chat("me")))
async def handle_message(client: Client, message: Message):
    text = message.text.lower()

    if text == '\U00002754' & isNotFakeScam(client, message):
        await client.send_message(chat_id=message.chat.id, text=config('ABOUT_ME'))
    elif re.search(r'расскажи о себе|расскажешь о себе', text) & (not message.from_user.is_self) & isNotFakeScam(client, message):
        await client.send_message(chat_id=message.chat.id, text=('Автоматическое сообщение: ' + config('ABOUT_ME')))


bot.run()