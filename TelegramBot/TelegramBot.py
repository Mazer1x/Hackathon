import asyncio
import requests
import uuid
import json
import pandas as pd
from aiogram import Bot, Dispatcher, F,types
from aiogram.filters import Command
from aiogram.types import Message

#! Constants
client_id = "fe68a59c-d14b-47dd-8dd1-892f9fec1258"
secret = "015e981c-ac21-462e-a02e-0747d383d7aa"
auth = "ZmU2OGE1OWMtZDE0Yi00N2RkLThkZDEtODkyZjlmZWMxMjU4OjQ3M2U5M2UyLTNiM2UtNGM3Yy1hOTIxLThiOWM5YWM3OWVmMg=="
TELEGRAM_TOKEN = "7291896984:AAEFagBoRTE795YnP_QhDQtpPZ9FEbiWCyo" 

#! Bot init
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

#! Helper functions
def get_token(auth_token, scope='GIGACHAT_API_PERS'):
    rq_uid = str(uuid.uuid4())
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }
    payload = {
        'scope': scope
    }
    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return -1

def get_chat_completion(auth_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat", 
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.4,
        "top_p": 0.1,
        "n": 1,
        "stream": False,
        "max_tokens": 2048,
        "repetition_penalty": 1,
        "update_interval": 0
    })

    headers = {
        'Content-Type': 'application/json', 
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}' 
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f"Произошла ошибка: {str(e)}")
        return -1

async def output_answer(message: Message, ifgive, data_raw):
    # Определяем verdict в зависимости от значения ifgive
    if ifgive == 0:
        verdict = "Один из последних в очереди на ипотеку"
    elif ifgive == -1:
        verdict = "Ни при каких условиях не может получить ипотеку"
    elif ifgive == 1:
        verdict = "Получает ипотеку"
    
    # Извлекаем данные из data_raw
    income_category = data_raw['income_category']
    gender = data_raw['gender']
    total_revolving_bal = data_raw['total_revolving_bal']
    total_relationship_count = data_raw['total_relationship_count']
    num_room = data_raw['num_room']
    
    # Генерация ответа на основе ifgive
    if ifgive == 1:
        answer = get_chat_completion(giga_token, 
                                     f'Клиент имеет следующие параметры: доход {income_category} руб., '
                                     f'Пола {gender}, c общим изменением баланса {total_revolving_bal}, '
                                     f'С {total_relationship_count} родственниками. Хочет взять в ипотеку '
                                     f'квартиру с {num_room} комнатами. Он {verdict}. '
                                     f'Почему ему позволили ее взять, дай КРАТКОЕ объяснение.')
        await message.answer(f"Почему человек получил ипотеку? <b>Объясняет Gigachat:</b>\n {answer.json()['choices'][0]['message']['content']}",parse_mode="HTML")
    elif ifgive == 0:
        answer = get_chat_completion(giga_token, 
                                     f'Клиент имеет следующие параметры: доход {income_category} руб., '
                                     f'Пола {gender}, c общим изменением баланса {total_revolving_bal}, '
                                     f'С {total_relationship_count} родственниками. Хочет взять в ипотеку '
                                     f'квартиру с {num_room} комнатами. Он {verdict}. '
                                     f'Почему ему позволили ее взять, дай КРАТКОЕ объяснение.')
        await message.answer(f"Почему человек один из последних в очереди на ипотеку? <b>Объясняет Gigachat:</b>\n {answer.json()['choices'][0]['message']['content']}",parse_mode="HTML")
    elif ifgive == -1:
        answer = get_chat_completion(giga_token, 
                                     f'Клиент имеет следующие параметры: доход {income_category} руб., '
                                     f'Пола {gender}, c общим изменением баланса {total_revolving_bal}, '
                                     f'С {total_relationship_count} родственниками. Хочет взять в ипотеку '
                                     f'квартиру с {num_room} комнатами. Он {verdict}. '
                                     f'Почему ему НЕ позволили ее взять, дай КРАТКОЕ объяснение.')
        await message.answer(f"Почему человек Ни при каких условиях не может получить ипотеку? <b>Объясняет Gigachat:</b>\n {answer.json()['choices'][0]['message']['content']}",parse_mode="HTML")

#! Handlers
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    await message.answer("Привет! Это бот команды 'Дайте стажировку'!\nКстати, уже подумали о предложении??? =) ")
    await message.answer("Чтобы получить информацию о клиенте, введите его ID из submission.csv")

@dp.message(F.text)
async def get_client_info(message: Message):
    userInput = message.text
    try:
        userId = int(userInput)
        data_raw = df_raw.loc[userId]
        ifgive = df_pr.loc[userId].iloc[-1]
        if float(ifgive)<0: ifgive = -1
        elif float(ifgive)==0: ifgive = 0
        elif float(ifgive)>0: ifgive = 1
        await output_answer(message,ifgive,data_raw)

    except Exception as ex:
        await message.answer(f"Произошла ошибка: {str(ex)}")

#! Main function
async def main():
    print("Бот запущен!")
    #! Get token
    response = get_token(auth)
    if response != -1:
        global giga_token
        giga_token = response.json()['access_token']
    
    #! Read CSV
    global df_pr,df_raw
    df_pr = pd.read_csv("done.csv",index_col="id")
    df_raw = pd.read_csv("raw.csv")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())