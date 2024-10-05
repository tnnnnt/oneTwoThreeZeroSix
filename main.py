import json
fs = '普宁'
ts = '深圳'
date = '2024-10-05'
with open('train.json', 'r', encoding='utf-8') as file:
    train_data = json.load(file)
with open('city.json', 'r', encoding='utf-8') as file:
    city_data = json.load(file)
print(train_data)
print(city_data)
