from fastapi import APIRouter, BackgroundTasks, Header, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    LocationAction)
from starlette.exceptions import HTTPException
from app import config
from app.facades.chatgpt import ChatGPT


line_bot_callback_router = APIRouter(prefix="", tags=["line_bot"])
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
chat = ChatGPT()


@line_bot_callback_router.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature=Header(None),
):
    """Line Bot用のエンドポイントです"""
    body = await request.body()

    try:
        background_tasks.add_task(
            handler.handle, body.decode("utf-8"), x_line_signature
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "ok"


@handler.add(MessageEvent)
def handle_message(event):
    if event.type != "message" or event.message.type != "text":
        return
    message = TextMessage(text=event.message.text)

    line_bot_api.reply_message(
        event.reply_token, create_message(message.text)
    )


def create_message(msg: str | None):
    if msg == "救援を要請する":
        reply = [
            TextMessage(text="救援要請を受け付けました。"),
            QuickReplyButton(action=LocationAction(label="location")),
        ]
        return TextSendMessage(text="位置情報を送信する。",
                               quick_reply=QuickReply(items=reply))
    else:
        return TextSendMessage(text=chat.request(msg))
