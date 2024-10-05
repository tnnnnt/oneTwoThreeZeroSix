import requests
import json

from_station = '普宁'
to_station_city = '深圳'
depart_date = '2024-10-07'

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
cookies = {
	'JSESSIONID': ''
}
response = requests.get(url_query_g, params=params_query_g, cookies=cookies)
if response.status_code == 200:
	try:
		datas_query_g = response.json()["data"]["result"]  # 解析 JSON 数据
	except ValueError:
		print("无法解析 JSON 响应")
		exit()
else:
	print(f"请求失败，状态码: {response.status_code}")
	exit()
url_query_by_train_no = "https://kyfw.12306.cn/otn/czxx/queryByTrainNo"
possible_train_datas = {}
for data_query_g in datas_query_g:
	tmp = data_query_g.split('|')
	train_no = tmp[2]
	train_number = tmp[3]
	to_station_telecode = tmp[7]
	start_time = tmp[8]
	end_time = tmp[9]
	duration_time = tmp[10]
	has_tickets = tmp[11]
	if has_tickets == 'Y':
		for k, v in train_data.items():
			if v["telecode"] == to_station_telecode:
				to_station = k
				break
		print('车次: {}, 出发站: {}, 到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
			train_number, from_station, to_station, start_time, end_time, duration_time))
		continue
	params_query_by_train_no = {
		'train_no': train_no,
		'from_station_telecode': from_station_telecode,
		'to_station_telecode': to_station_telecode,
		'depart_date': depart_date
	}
	response = requests.get(url_query_by_train_no, params=params_query_by_train_no)
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
		response = requests.get(url_query_g, params=params_query_g, cookies=cookies)
		if response.status_code == 200:
			try:
				datas_query_g_tmp = response.json()["data"]["result"]  # 解析 JSON 数据
			except ValueError:
				print('------')
				print("无法解析 JSON 响应")
				print('------')
				continue
		else:
			print('------')
			print(f"请求失败，状态码: {response.status_code}")
			print('------')
			continue
		for data_query_g_tmp in datas_query_g_tmp:
			tmp = data_query_g_tmp.split('|')
			train_no = tmp[2]
			to_station_telecode = tmp[7]
			has_tickets = tmp[11]
			if train_no not in v['train_no_list'] or to_station_telecode != to_station_telecode_tmp or has_tickets == 'N':
				continue
			train_number = tmp[3]
			start_time = tmp[8]
			end_time = tmp[9]
			duration_time = tmp[10]
			print('车次: {}, 出发站: {}, 到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
				train_number, k, to_station_tmp, start_time, end_time, duration_time))
