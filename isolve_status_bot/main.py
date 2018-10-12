import asyncio
import aiogram
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from band import worker, cleanup, logger, settings
from asimplech import ClickHouse
import arrow
import datetime
import dateutil.parser
import json


TOKEN = str(settings.TOKEN)
WEBHOOK_HOST = str(settings.WEBHOOK_HOST)
WEBHOOK_URL_PATH = str(settings.WEBHOOK_URL_PATH)
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_URL_PATH}"
MY_USER_ID = str(settings.MY_USER_ID)

bot = Bot(TOKEN)
dp = Dispatcher(bot)

ch = ClickHouse()

@worker()
async def worker():
    logger.info('isolve_status_bot has been started')
    # Get current webhook status
    webhook = await bot.get_webhook_info()
    logger.error(f'Old webhook: {webhook}')
    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        if not webhook.url:
            await bot.delete_webhook()
        # Set new URL for webhook
        await bot.set_webhook(WEBHOOK_URL)
    await status_checker()


async def status_checker():
    while True:
        curr_date_in_ch = await get_actual_server_status()
        if curr_date_in_ch != None:
            diff_in_min = ((datetime.datetime.now() + datetime.timedelta(hours=3)) - curr_date_in_ch).seconds / 60
            logger.debug('Actual difference in data is {}'.format(diff_in_min))
            if diff_in_min > 15:
                await bot.send_message(MY_USER_ID, "!!!! Данные на сервере не актуальны !!!! \n Последняя запись от: {}".format(curr_date_in_ch.strftime('%d-%m-%Y %H:%M:%S')))
        else:
            await bot.send_message(MY_USER_ID, "Боту хреново! Спаси бота!")
        # Wait explicit time
        next_at = arrow.utcnow().shift(minutes=+15)
        wait_secs = next_at.timestamp - arrow.utcnow().timestamp
        logger.debug("waiting {} seconds".format(wait_secs))
        await asyncio.sleep(wait_secs)


async def get_actual_server_status():
    query = """
    SELECT MAX(dateTime) as last_point FROM events FORMAT JSON
    """
    try:
        res = await ch.select(query)
        # datetime.timedelta(hours=3) - поправка на Москву
        curr_date_in_ch = dateutil.parser.parse(json.loads(res)['data'][0]['last_point']) + datetime.timedelta(hours=3)
        return curr_date_in_ch
    except Exception as ex:
        logger.error('CH exception: {}'.format(ex))
        return None


@cleanup()
async def on_shutdown():
    """
    Graceful shutdown. This method is recommended by aiohttp docs.
    """
    # Remove webhook.
    await bot.delete_webhook()