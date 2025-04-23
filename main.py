import logging
import logging.handlers
import re
import random
from decouple import config
from pyrogram  import Client, filters, enums
from pyrogram.types import Message
from yandex_music import ClientAsync as YandexMusicClient
from g4f.client import AsyncClient as AiClient
from g4f.Provider import PollinationsAI

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

try:
    ai_client = AiClient(provider=PollinationsAI, media_provider=PollinationsAI)
except Exception as e:
    logging.error(f"Ошибка при инициализации Ai клиента: {e}")
    ai_client = None

async def isNotFakeScam(client: Client, message: Message):
    user = message.from_user
    if (user.is_fake | user.is_scam):
        await client.send_message(chat_id="me", text=f"Пользователь {user.username} помечен как фейк/скам")
        return False
    
    return True


@bot.on_message(filters.text and (filters.private or filters.chat("me") or filters.user("me")))
async def handle_message(client: Client, message: Message):
    text = message.text.lower() if message.text is not None else ''
    isMeOrContact = message.from_user.is_self or message.from_user.is_contact

    if (text == '\U00002754') and await isNotFakeScam(client, message):
        answer = await message.reply(text=config('ABOUT_ME'), quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    elif (re.search(r'расскажи о себе|расскажешь о себе', text) != None) and (not message.from_user.is_self) and await isNotFakeScam(client, message):
        answer = await message.reply(chat_id=message.chat.id, text=f'**Автоматическое сообщение:**\n{config("ABOUT_ME")}', parse_mode=enums.ParseMode.MARKDOWN, quote=True)
        await client.pin_chat_message(answer.chat.id, answer.id)
    
    if message.from_user.is_self and ("\U00002754" in text):
        user_id = text.split("\U00002754")[1].strip()

        if user_id.count < 2:
            return 

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
            logging.error(f"Ошибка при получении информации о пользователе: {e}")
            
    if (text == "песня из мне нравится" or text == "музыка из мне нравится") and isMeOrContact:
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
                logging.error(f"Ошибка при получении песни из Yandex Music: {e}")
        else:
            logging.error(f'Yandex Music API не инициализирован.')

    if 'ии:' in text and isMeOrContact:

        if not ai_client:
            return

        prompt = text.split('ии:')[1].strip()

        if len(prompt) < 2:
            return
        
        try:
            response = await ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            await message.reply(text=response.choices[0].message.content, parse_mode=enums.ParseMode.MARKDOWN, quote=True)
        except Exception as e:
            logging.error(f"Ошибка при получении запроса от ИИ: {e}")

    if 'нарисуй:' in text and isMeOrContact:

        if not ai_client:
            return

        prompt = text.split('нарисуй:')[1].strip()

        if len(prompt) < 2:
            return
        
        try:
            created_message = await client.send_message(chat_id=message.chat.id, text="Создаю", reply_to_message_id=message.id, disable_notification=True)
            response = await ai_client.images.async_generate(
                prompt=prompt,
                model="flux-schnell",
                response_format="url",
            )

            url = response.data[0].url

            await client.send_photo(message.chat.id, url, reply_to_message_id=message.id)
        except Exception as e:
            logging.error(f"Ошибка при получении изображения от ИИ: {e}")
        finally:
            if created_message != None:
                await client.delete_messages(message.chat.id, created_message.id)


bot.run()