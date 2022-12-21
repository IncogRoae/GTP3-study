import boto3
import csv
from config import aws_access_key, aws_secret_key

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2', aws_access_key_id=aws_access_key,
                              aws_secret_access_key=aws_secret_key)
table_name = 'gpt_table'

# 학습을 위한 data set을 json으로 변환
def make_json():
    data = {}
    with open(r'data.csv', encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for rows in csvReader:
            data[rows['key']] = rows['text']

    return data

# DynamoDB full scan
def select_all():
    table = dynamodb.Table(table_name)
    return table.scan()

# DynamoDB에 데이터 추가 로직
def insert_a_row(row):
    table = dynamodb.Table(table_name)
    print(table.put_item(Item=row))


if __name__ == '__main__':
    for k, v in make_json().items():
        row = {
            'key': k,
            'text': v
        }
        insert_a_row(row)