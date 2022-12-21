import openai
import json
from db import select_all
from datetime import datetime, timedelta
from config import api_key

# openai secret key
openai.api_key = api_key

# DynamoDB에서 데이터를 스캔해 특정 개수만큼 추출하여 jsonl 파일로 변환 후 로컬에 저장
def convert_CSV_to_JSONL():
    row_data = list()
    items = select_all()['Items']
    for index in range(0, 3000):
        rnd_data = items[index]
        row_data.append({'prompt': rnd_data['key'], 'completion': rnd_data['text']})

    with open("data.jsonl", encoding="utf-8", mode="w") as file:
        for i in row_data:
            file.write(json.dumps(i, ensure_ascii=False) + "\n")

# jsonl 파일을 openai 서버에 파일로 업로드 하는 로직
def upload_file():
    response = openai.File.create(file=open("data.jsonl", "rb"), purpose="fine-tune")
    return response["id"]

# 업로드 된 파일을 기반으로 fine-tuned 작업을 하는 로직
def fine_tuning(file):
    response = openai.FineTune.create(training_file=file, model='davinci') # 별도로 model 파라미터를 생성하여 지정 가능
    date = datetime.now() + timedelta(microseconds=response["created_at"]/10) - timedelta(hours=9)
    print(f"davinci:ft-personal-{date.strftime('%Y-%m-%d-%H-%M-%S')}")

    # fine-tuned 결과 모델 명이 'created_at'을 기준으로 생성되기 때문에 맞춰서 파싱
    return f"davinci:ft-personal-{date.strftime('%Y-%m-%d-%H-%M-%S')}"

# 입력된 prompt를 기반으로 결과를 생성하는 로직
def gpt3_interaction(ask, history, model):
    prompt_initial = f"User:%s\nBOT:" % (ask)

    # 이전 대화를 기반으로 프롬프트를 누적
    prompt = history + "\n" + prompt_initial

    # 프롬프트를 기반으로 실제 데이터를 생성하기 위해 request를 보내는 로직
    response = openai.Completion.create(
                                        #model=model,               # 어떤 학습된 모델을 사용할지 명시
                                        model="text-davinci-003",   # davinci, curie, babbage, ada의 기본 모델 혹은 fine tuning으로 커스텀한 모델 사용 가능
                                        prompt=prompt,              # 명령 프롬프트
                                        max_tokens=500,             # 완료시 생성할 최대 토큰 (Free tier는 2048)
                                        temperature=0.3,            # 0~1, 값이 1에 가까울수록 AI가 학습된 데이터를 기반으로 더 창의적인 결과를 도출
                                        top_p=1.0,                  # 0~1, temperature와 비슷하게 결과값이 얼마나 결정적인지 즉, 얼마나 명확하지 않게 할 것인지
                                                                    # 학습된 모델을 기반으로 명확한 대답을 도출할지 새로운 대답을 도출해낼지에 대한 값
                                        best_of=1,                  # 여러개의 결과중 가장 우수한 n개를 추출
                                        stop=["DONE"])              # 중지 시퀀스
    result = response.choices[0]['text']
    history = prompt + result

    print('BOT: %s\n' % (result))
    return result, history


if __name__ == '__main__':
    # 시작할 때 마다 튜닝 데이터 생성
    convert_CSV_to_JSONL()
    file_id = upload_file()
    ft_id = fine_tuning(file_id)

    # 최초 실행시엔 이전 대화 기록이 없어 별도 처리
    prompt = input("User: ")
    result, history = gpt3_interaction(ask=prompt, history='', model=ft_id)
    while True:
        # 이후 영구적으로 대화 핑
        prompt = input("User: ")
        if "exit" in prompt.lower():
            exit()

        result, history = gpt3_interaction(ask=prompt, history=history, model=ft_id)
