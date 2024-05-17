import os
import dotenv
import logging
import openai
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextSendMessage, TextMessage
from linebot.exceptions import InvalidSignatureError

dotenv.load_dotenv()
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
openai_api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI()
logger = logging.getLogger('uvicorn')

linebot = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI APIの設定
openai.api_key = openai_api_key


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    logger.info(body.decode())
    try:
        handler.handle(body.decode(), request.headers['x-line-signature'])
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail='InvalidSignatureError')

    return 'ok'


@handler.add(MessageEvent, TextMessage)
def handle_message(event):
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {
                "role": "system",
                "content": "日本語で応答してください"
            },
            {
                "role": "user",
                "content": event.message.text
            }
        ]
    )
    # ChatCPTの応答をLINEに返す
    chat_response = response.choices[0].message.content
    res_message = TextSendMessage(text=chat_response)
    linebot.reply_message(event.reply_token, res_message)
