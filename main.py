import logging
import logging.handlers
import re
import random
from decouple import config
from pyrogram  import Client, filters, enums
from pyrogram.types import Message, Chat
from yandex_music import ClientAsync as YandexMusicClient

logging.basicConfig(level=logging.INFO, filename="logs.txt", filemode="a", format="%(asctime)s %(levelname)s %(message)s")
logging.handlers.RotatingFileHandler("logs.txt", maxBytes=2048, backupCount=2)

logging.info("Start!")

bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'))

try:
    ym_client = YandexMusicClient(config('YANDEX_MUSIC_TOKEN'), language='ru')
    ym_client.init()
except Exception as e:
    logging.error(f"Ошибка при инициализации Yandex Music API: {e}")
    ym_client = None

async def isNotFakeScam(client: Client, message: Message):
    user = message.from_user
    if (user.is_fake | user.is_scam):
        await client.send_message(chat_id="me", text=f"Пользователь {user.username} помечен как фейк/скам")
        return False
    
    return True


@bot.on_message(filters.text & (filters.private | filters.chat("me")))
async def handle_message(client: Client, message: Message):
    text = message.text.lower()
    isMeOrContact = message.from_user.is_self | message.from_user.is_contact

    if (text == '\U00002754') & await isNotFakeScam(client, message):
        answer = await message.reply(text=config('ABOUT_ME'), quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    elif (re.search(r'расскажи о себе|расскажешь о себе', text) != None) & (not message.from_user.is_self) & await isNotFakeScam(client, message):
        answer = await message.reply(chat_id=message.chat.id, text=f'**Автоматическое сообщение:**\n{config("ABOUT_ME")}', parse_mode=enums.ParseMode.MARKDOWN, quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    
    if message.from_user.is_self & ("\U00002754" in text):
        user_id = text.split("\U00002754")[1].strip()
        try:
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

                await message.reply(text=f'**Пользователь:** {user.username}\n'
                         f'**Имя:** {user.first_name}\n'
                         f'**Фамилия:** {user.last_name}\n'
                         f'**Метки:** {flags}\n'
                         f'**Код страны:** {user.language_code or "Не указано"}\n'
                         f'**Последняя дата в сети:** {last_online}',
                    parse_mode=enums.ParseMode.MARKDOWN, quote=True)
            
        except Exception as e:
            logging.error(f"**Ошибка при получении информации о пользователе:**\n{e}")
            
    if (text == "песня из мне нравится" or text == "музыка из мне нравится") & isMeOrContact :
        if ym_client:
            try:
                playlist_tracks = await ym_client.users_likes_tracks()
                
                if not playlist_tracks.tracks:
                    await message.reply(
                        text='**В плейлисте "Мне нравится" нет песен.**',
                        parse_mode=enums.ParseMode.MARKDOWN,
                        quote=True
                    )
                    return
                
                random_track = await random.choice(playlist_tracks.tracks).fetch_track_async()
                
                track_name = random_track.title
                artist_name = ', '.join([artist.name for artist in random_track.artists])
                track_url = f"https://music.yandex.ru/track/{random_track.id}"

                await message.reply(
                    text=f'**Вот случайная песня из плейлиста "Мне нравится":**\n'
                         f'[{track_name} - {artist_name}]({track_url})',
                    parse_mode=enums.ParseMode.MARKDOWN,
                    quote=True
                )
            except Exception as e:
                logging.error(f"**Ошибка при получении песни из Yandex Music:**\n{e}")
        else:
            logging.error(f'*Yandex Music API не инициализирован.*')
    


bot.run()