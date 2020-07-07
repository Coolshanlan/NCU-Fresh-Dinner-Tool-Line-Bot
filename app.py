# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import os
import re
import requests
import torch
from datetime import date, datetime
import numpy as np
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
from urllib.parse import parse_qs
import csv
import openpyxl as op
# import imgurfile
from imgurpython import ImgurClient
from linebot.models.template import *
from linebot.models.template import (
    ButtonsTemplate, CarouselTemplate, ConfirmTemplate, ImageCarouselTemplate
)
from linebot.models import (
    PostbackEvent
)
from linebot.models import (
    FollowEvent
)
from linebot.models import (
    ImagemapSendMessage, TextSendMessage, ImageSendMessage, LocationSendMessage, FlexSendMessage, VideoSendMessage
)
import json
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage
)
from flask import Flask, request, abort
from IPython import get_ipython

# %%
# get_ipython().system('pip install flask')
# get_ipython().system('pip install line-bot-sdk')


# %%
'''

整體功能描述

應用伺服器主結構樣板
    用來定義使用者傳送消息時，應該傳到哪些方法上
        比如收到文字消息時，轉送到文字專屬處理方法

消息專屬方法定義
    當收到文字消息，從資料夾內提取消息，並進行回傳。

啟動應用伺服器

'''


# %%
'''

Application 主架構

'''

# 引用Web Server套件

# 從linebot 套件包裡引用 LineBotApi 與 WebhookHandler 類別

# 引用無效簽章錯誤

# 載入json處理套件

# 載入基礎設定檔
secretFileContentJson = json.load(
    open("./line_secret_key", 'r', encoding='utf8'))

# 設定Server啟用細節
app = Flask(__name__, static_url_path="/material", static_folder="./material/")

# 生成實體物件
line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))
handler = WebhookHandler(secretFileContentJson.get("secret_key"))

# 啟動server對外接口，使Line能丟消息進來


@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# %%
'''

消息判斷器

讀取指定的json檔案後，把json解析成不同格式的SendMessage

讀取檔案，
把內容轉換成json
將json轉換成消息
放回array中，並把array傳出。

'''

# 引用會用到的套件


def detect_json_array_to_new_message_array(fileName):

    # 開啟檔案，轉成json
    with open(fileName, 'r', encoding='utf8') as f:
        jsonArray = json.load(f)

    # 解析json
    returnArray = []
    for jsonObject in jsonArray:

        # 讀取其用來判斷的元件
        message_type = jsonObject.get('type')

        # 轉換
        if message_type == 'text':
            returnArray.append(TextSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'imagemap':
            returnArray.append(
                ImagemapSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'template':
            returnArray.append(
                TemplateSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'image':
            returnArray.append(ImageSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'sticker':
            returnArray.append(
                StickerSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'audio':
            returnArray.append(AudioSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'location':
            returnArray.append(
                LocationSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'flex':
            returnArray.append(FlexSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'video':
            returnArray.append(VideoSendMessage.new_from_json_dict(jsonObject))

    # 回傳
    return returnArray


# %%
'''

handler處理關注消息

用戶關注時，讀取 素材 -> 關注 -> reply.json

將其轉換成可寄發的消息，傳回給Line

'''

# 引用套件

# 關注事件處理

# %%
'''

handler處理文字消息

收到用戶回應的文字消息，
按文字消息內容，往素材資料夾中，找尋以該內容命名的資料夾，讀取裡面的reply.json

轉譯json後，將消息回傳給用戶

'''

# 引用套件


@handler.add(MessageEvent, message=ImageMessage)
def process_image_message(event):
    result_message_array = []
    response = requests.get(
        f"https://api.line.me/v2/bot/message/{event.message.id}/content", stream=True, headers={'Authorization': f'Bearer {secretFileContentJson.get("channel_access_token")}'})

    img = Image.open(response.raw)
    filepath = f"predection/{event.message.id}.{img.format.lower()}"
    img.save(filepath)
    result_message_array.append(TextSendMessage(text="好歐收到囉~"))
    line_bot_api.reply_message(
        event.reply_token,
        result_message_array
    )


def updatemax():
    global usermax, dinnermax, dinnerlist, userlist, usersheet, dinnersheet
    usermax = usersheet.max_row
    dinnermax = dinnersheet.max_row
    dinnerlist = [[b.value for b in i] for i in list(dinnersheet.rows)]
    userlist = [[b.value for b in i] for i in list(usersheet.rows)]


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    global filepath, today_date, storeName, FoodMessaage
    if event.message.text == "格式":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="餐點/價格/價差")
        )
        return
    if event.message.text == "今天吃什麼":

        line_bot_api.reply_message(
            event.reply_token,
            FoodMessaage
        )
        return
    user_id = event.source.user_id.replace("\n", "")
    user_info = [i for i in userlist if i[0].replace("\n", "") == user_id]
    user_index = -1
    for index, i in enumerate(userlist):
        if i[0].replace("\n", "") == user_id:
            user_index = index
            break
    if user_info == []:
        usersheet[f"A{usermax+1}"] = user_id
        usersheet[f"B{usermax+1}"] = event.message.text
        wb.save(filepath)
        updatemax()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{user_id} {event.message.text} 已登錄")
        )
        print(f"登陸：{event.message.text}/{user_id}")
    else:
        user_info = user_info[0]
        testinfo = event.message.text.split("/")
        if len(testinfo) != 3:
            usersheet[f"D{user_index+1}"] = event.message.text
            wb.save(filepath)
            updatemax()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="我看不懂耶QQ")
            )
            return
        nowtime = datetime.now().strftime("%H:%M")
        dinnersheet[f"A{dinnermax+1}"] = today_date
        dinnersheet[f"B{dinnermax+1}"] = nowtime
        dinnersheet[f"C{dinnermax+1}"] = storeName
        dinnersheet[f"D{dinnermax+1}"] = user_info[1]
        dinnersheet[f"E{dinnermax+1}"] = testinfo[0]
        dinnersheet[f"F{dinnermax+1}"] = testinfo[1]
        dinnersheet[f"G{dinnermax+1}"] = testinfo[2]
        wb.save(filepath)
        updatemax()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{user_info[1]} 飢餓精靈收到囉！")
        )
        print(
            f"點餐：{today_date}/{nowtime}/{storeName}/{user_info[1]}/{testinfo[0]}/{testinfo[1]}/{testinfo[2]}")


# %%
'''

Application 運行（開發版）

'''
filepath = "C:\\User_D\\Program\\Project_Python\\ncufresh_dinnertool\\DinnerList.xlsx"
wb = op.load_workbook(filepath)
usersheet = wb["UserList"]
dinnersheet = wb["DinnerList"]
usermax = usersheet.max_row
dinnermax = dinnersheet.max_row
dinnerlist = [i[0].value for i in list(dinnersheet.rows)]
userlist = [i[0].value for i in list(usersheet.rows)]
storeName = "Test"
# print(userlist)
today_date = date.today()
FoodMessaage = []
subsidy = 100
imagepath = "https://image.shutterstock.com/image-photo/healthy-food-clean-eating-selection-260nw-722718097.jpg"
# ImageSendMessage(original_content_url='圖片網址', preview_image_url='圖片網址')
FoodMessaage.append(ImageSendMessage(
    original_content_url=imagepath, preview_image_url=imagepath))
FoodMessaage.append(TextSendMessage(text=f"補助：{subsidy}"))
updatemax()
if __name__ == "__main__":
    # imgur_client = imgurfile.setauthorize()
    # for i in range(15):
    #     acc, loss = FSA.train()
    #     acc = round(acc, 4)
    #     loss = round(loss, 4)
    #     print(f"loss:{loss}  acc:{acc}")
    # process_image_message(None)
    app.run(host='0.0.0.0')


# %%
'''

Application 運行（heroku版）

'''

# if __name__ == "__main__":
#     imgur_client = imgurfile.setauthorize()
#     app.run(host='0.0.0.0', port=os.environ['PORT'])


# %%
