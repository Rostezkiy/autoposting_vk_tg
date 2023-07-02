import logging.config
import requests
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

logging.config.fileConfig('logging.ini')
logger = logging.getLogger()

vk_access_token = config.get('VK', 'token')
vk_group_id = config.get('VK', 'group_id')
telegram_token = config.get('TG', 'token')
telegram_channel_id = config.get('TG', 'channel_id')


def send_message_to_telegram(message):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    data = {
        'chat_id': telegram_channel_id,
        'text': message,
        'parse_mode': 'HTML',  # Указываем, что сообщение содержит HTML-разметку
        'disable_web_page_preview': True  # Отключаем отображение ссылки на запись VK
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        logger.info('Message sent successfully')
    else:
        logger.error('Failed to send message: %s', response.text)


def send_photos_to_telegram(photo_urls, caption):
    media = []
    for i, photo_url in enumerate(photo_urls):
        media.append({
            'type': 'photo',
            'media': photo_url,
        })
        if i == 0:  # add caption only to the first photo
            media[0]['caption'] = caption
    url = f'https://api.telegram.org/bot{telegram_token}/sendMediaGroup'
    data = {
        'chat_id': telegram_channel_id,
        'media': json.dumps(media),
        'message': caption,
        'parse_mode': 'HTML',
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        logger.info('Photos sent successfully')
    else:
        logger.error('Failed to send photos: %s', response.text)


def get_long_poll_server():
    url = 'https://api.vk.com/method/groups.getLongPollServer'
    params = {
        'group_id': vk_group_id,
        'access_token': vk_access_token,
        'v': '5.131'
    }
    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200:
        logger.debug('Successfully got long poll server data')
    else:
        logger.error('Failed to get long poll server data: %s', response.text)

    return data['response']


def listen_long_poll_server(server, key, ts):
    url = f"{server}?act=a_check&key={key}&ts={ts}&wait=25"
    response = requests.get(url)

    if response.status_code == 200:
        data = json.loads(response.text)
        try:
            ts = data['ts']
        except KeyError:
            logger.error('Failed to get "ts" key from data: %s', data)
            return listen_long_poll_server(server, key, ts)

        for update in data['updates']:
            if update['type'] == 'wall_post_new':
                post_id = update['object']['id']
                text = update['object']['text']
                attachments = []
                for attachment in update['object'].get('attachments', []):
                    if attachment['type'] == 'photo':
                        photo = attachment['photo']
                        largest_size = max(photo['sizes'], key=lambda s: s['width'])
                        attachments.append(largest_size['url'])
                post_url = f"https://vk.com/wall-{vk_group_id}_{post_id}"
                if len(text) > 1024:
                    sentences = text.split('.')
                    first_sentence = sentences[0]
                    # short caption with link "Читать полностью"
                    message = f"{first_sentence}...\n\n—\n<a href='{post_url}'>Читать полностью</a>"
                    if attachments:
                        caption = f"{first_sentence}...\n\n—\nЧитать полностью > '{post_url}'"
                        send_photos_to_telegram(attachments, caption)
                    else:
                        send_message_to_telegram(message)
                else:
                    message = f"{text} \n\n—\n<a href='{post_url}'>Открыть запись</a>"
                    if attachments:
                        caption = f"{text} \n\n—\n'Открыть запись > {post_url}'"
                        send_photos_to_telegram(attachments, caption)
                    else:
                        send_message_to_telegram(message)
        listen_long_poll_server(server, key, ts)
    elif response.status_code == 201:
        data = json.loads(response.text)
        try:
            ts = data['ts']
        except KeyError:
            logger.error('Failed to get "ts" key from data: %s', data)
            logger.warning('Restarting long polling')
            return start_long_polling
        logger.info('Restarting long polling')
        listen_long_poll_server(server, key, ts)
    elif response.status_code == 204:
        listen_long_poll_server(server, key, ts)
    else:
        logger.error('Failed to listen long poll server: %s', response.text)


def start_long_polling():
    logger.info('Starting application')
    long_poll_server = get_long_poll_server()
    server = long_poll_server['server']
    key = long_poll_server['key']
    ts = long_poll_server['ts']
    logger.debug(f'Data: server={server}, key={key}, ts={ts}')
    listen_long_poll_server(server, key, ts)


start_long_polling()