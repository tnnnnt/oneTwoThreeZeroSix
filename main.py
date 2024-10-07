import requests
import json
import time

# 下一步更新：爬价格、过滤出发时间和到达时间、实际终点

from_station = '普宁'
to_station_city = '深圳'
depart_date = '2024-10-10'
time_sleep = 5
chance = 3
headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
	'Accept': 'application/json, text/javascript, */*; q=0.01',
	'Accept-Encoding': 'gzip, deflate, br, zstd',
	'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
	'Cache-Control': 'no-cache',
	'Connection': 'keep-alive',
	'X-Requested-With': 'XMLHttpRequest'
}
cookies = {
	'JSESSIONID': ''
}
with open('train.json', 'r', encoding='utf-8') as file:
	train_data = json.load(file)
with open('city.json', 'r', encoding='utf-8') as file:
	city_data = json.load(file)
to_station = city_data[to_station_city][0]
from_station_telecode = train_data[from_station]['telecode']
to_station_telecode = train_data[to_station]['telecode']
url_query_g = "https://kyfw.12306.cn/otn/leftTicket/queryG"
params_query_g = {
	'leftTicketDTO.train_date': depart_date,
	'leftTicketDTO.from_station': from_station_telecode,
	'leftTicketDTO.to_station': to_station_telecode,
	'purpose_codes': 'ADULT'
}
chance_no = 1
while True:
	try:
		response = requests.get(url_query_g, headers=headers, params=params_query_g, cookies=cookies)
		response.raise_for_status()  # 如果状态码不是 200，抛出异常
		datas_query_g = response.json()["data"]["result"]  # 解析 JSON 数据
		break
	except Exception as e:
		print(e)
	if chance_no == chance:
		exit()
	chance_no += 1
	time.sleep(time_sleep)
url_query_by_train_no = "https://kyfw.12306.cn/otn/czxx/queryByTrainNo"
possible_train_datas = {}
seat_type = {"A": "高级动卧", "B": "混编硬座", "C": "混编硬卧", "D": "优选一等座", "E": "特等软座", "F": "动卧", "G": "二人软包", "H": "一人软包", "I": "一等卧", "J": "二等卧", "K": "混编软座", "L": "混编软卧", "M": "一等座", "O": "二等座", "P": "特等座", "Q": "多功能座", "S": "二等包座", "W": "无座", "0": "棚车", "1": "硬座", "2": "软座", "3": "硬卧", "4": "软卧", "5": "包厢硬卧", "6": "高级软卧", "7": "一等软座", "8": "二等软座", "9": "商务座"}
for data_query_g in datas_query_g:
	tmp = data_query_g.split('|')
	train_no = tmp[2]
	to_station_telecode = tmp[7]
	has_tickets = tmp[11]
	if has_tickets == 'Y':
		train_number = tmp[3]
		start_time = tmp[8]
		end_time = tmp[9]
		duration_time = tmp[10]
		ticket_stock_and_price = tmp[39]
		for k, v in train_data.items():
			if v["telecode"] == to_station_telecode:
				to_station = k
				break
		print('车次: {}, 出发站: {}, 到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
			train_number, from_station, to_station, start_time, end_time, duration_time))
		for i in range(0, len(ticket_stock_and_price), 10):
			t = ticket_stock_and_price[i:i+10]
			if t[7:] != '000':
				print(seat_type[t[0]], end='')
				if t[6] == '3':
					print('(无座)', end='')
				print('\t￥'+t[1:5]+'.'+t[5]+'\t余票', end='')
				print(t[7:]+'张')
		continue
	params_query_by_train_no = {
		'train_no': train_no,
		'from_station_telecode': from_station_telecode,
		'to_station_telecode': to_station_telecode,
		'depart_date': depart_date
	}
	response = requests.get(url_query_by_train_no, headers=headers, params=params_query_by_train_no, cookies=cookies)
	if response.status_code == 200:
		try:
			datas_station_name = response.json()['data']['data']  # 解析 JSON 数据
			station_names = []
			from_station_ind = -1
			for data_station_name in datas_station_name:
				if data_station_name['station_name'] == from_station:
					from_station_ind = len(station_names)
				station_names.append(data_station_name['station_name'])
			for from_ind in range(from_station_ind + 1):
				if station_names[from_ind] not in possible_train_datas:
					possible_train_datas[station_names[from_ind]] = {'train_no_list': [], 'to_station_list': []}
				possible_train_datas[station_names[from_ind]]['train_no_list'].append(train_no)
				for to_ind in range(from_station_ind + 1, len(station_names)):
					if station_names[to_ind] == '汕  头':  # 就你汕头搞特殊，害我出bug！
						station_names[to_ind] = '汕头'
					if station_names[to_ind] not in possible_train_datas[station_names[from_ind]]['to_station_list']:
						possible_train_datas[station_names[from_ind]]['to_station_list'].append(station_names[to_ind])
		except ValueError:
			print('------')
			print("无法解析 JSON 响应")
			print(tmp)
			print('------')
			continue
	else:
		print('------')
		print(f"请求失败，状态码: {response.status_code}")
		print(tmp)
		print('------')
		continue
for k, v in possible_train_datas.items():
	from_station_telecode_tmp = train_data[k]['telecode']
	to_station_list = v['to_station_list']
	for to_station_tmp in to_station_list:
		to_station_telecode_tmp = train_data[to_station_tmp]['telecode']
		params_query_g['leftTicketDTO.from_station'] = from_station_telecode_tmp
		params_query_g['leftTicketDTO.to_station'] = to_station_telecode_tmp
		chance_no = 1
		while True:
			try:
				response = requests.get(url_query_g, headers=headers, params=params_query_g, cookies=cookies)
				response.raise_for_status()  # 如果状态码不是 200，抛出异常
				datas_query_g_tmp = response.json()["data"]["result"]  # 解析 JSON 数据
				break
			except Exception as e:
				print(e)
			if chance_no == chance:
				exit()
			chance_no += 1
			time.sleep(time_sleep)
		for data_query_g_tmp in datas_query_g_tmp:
			tmp = data_query_g_tmp.split('|')
			train_no = tmp[2]
			to_station_telecode = tmp[7]
			has_tickets = tmp[11]
			if train_no not in v[
				'train_no_list'] or to_station_telecode != to_station_telecode_tmp or has_tickets == 'N':
				continue
			train_number = tmp[3]
			start_time = tmp[8]
			end_time = tmp[9]
			duration_time = tmp[10]
			ticket_stock_and_price = tmp[39]
			print('车次: {}, 出发站: {}, 到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
				train_number, k, to_station_tmp, start_time, end_time, duration_time))
			for i in range(0, len(ticket_stock_and_price), 10):
				t = ticket_stock_and_price[i:i+10]
				if t[7:] != '000':
					print(seat_type[t[0]], end='')
					if t[6] == '3':
						print('(无座)', end='')
					print('\t￥'+t[1:5]+'.'+t[5]+'\t余票', end='')
					print(t[7:]+'张')
