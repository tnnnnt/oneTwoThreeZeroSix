import requests
import json
import time

# 接下来要更新的内容
# 封装并优化一下
# 研究：Expecting value: line 1 column 1 (char 0)
# 票面出发时间、票面到达时间、实际出发时间、实际到达时间
# 票面价格、是否需要补票、补票后预估价格
# 过滤出发时间、到达时间、历时、是否需要补票、价格、实际终点
# 过滤高铁站


def make_request(url, headers, cookies, params, max_retries, sleep_time):
	chance_no = 1
	while True:
		try:
			response = requests.get(url, headers=headers, cookies=cookies, params=params)
			response.raise_for_status()  # 如果状态码不是 200，抛出异常
			return response.json()
		except Exception as ex:
			print(ex)
		if chance_no == max_retries:
			return {}
		chance_no += 1
		time.sleep(sleep_time)


def get_train_data_str_list(headers, cookies, max_retries, sleep_time, depart_date, from_station_telecode, to_station_telecode):
	# to get train data, its format is a lot of string with '|'
	url = "https://kyfw.12306.cn/otn/leftTicket/queryG"
	params = {
		'leftTicketDTO.train_date': depart_date,
		'leftTicketDTO.from_station': from_station_telecode,
		'leftTicketDTO.to_station': to_station_telecode,
		'purpose_codes': 'ADULT'
	}
	response_json = make_request(url, headers, cookies, params, max_retries, sleep_time)
	return response_json.get('data', {}).get('result', [])


def get_datas_station_name(headers, cookies, max_retries, sleep_time, train_no, from_station_telecode, to_station_telecode, depart_date):
	# get the station list of this train number
	url = "https://kyfw.12306.cn/otn/czxx/queryByTrainNo"
	params = {
		'train_no': train_no,
		'from_station_telecode': from_station_telecode,
		'to_station_telecode': to_station_telecode,
		'depart_date': depart_date
	}
	response_json = make_request(url, headers, cookies, params, max_retries, sleep_time)
	return response_json.get('data', {}).get('data', [])


if __name__ == "__main__":
	from_station = '普宁'
	to_city = '深圳'
	depart_date = '2024-10-19'
	sleep_time = 5
	max_retries = 3
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
	to_station = city_data[to_city][0]
	from_station_telecode = train_data[from_station]['telecode']
	to_station_telecode = train_data[to_station]['telecode']
	train_data_str_list = get_train_data_str_list(headers, cookies, max_retries, sleep_time, depart_date, from_station_telecode, to_station_telecode)
	if not len(train_data_str_list):
		exit()
	url_query_by_train_no = "https://kyfw.12306.cn/otn/czxx/queryByTrainNo"
	possible_train_datas = {}
	seat_type = {"A": "高级动卧", "B": "混编硬座", "C": "混编硬卧", "D": "优选一等座", "E": "特等软座", "F": "动卧",
				 "G": "二人软包", "H": "一人软包", "I": "一等卧", "J": "二等卧", "K": "混编软座", "L": "混编软卧",
				 "M": "一等座", "O": "二等座", "P": "特等座", "Q": "多功能座", "S": "二等包座", "W": "无座",
				 "0": "棚车", "1": "硬座", "2": "软座", "3": "硬卧", "4": "软卧", "5": "包厢硬卧", "6": "高级软卧",
				 "7": "一等软座", "8": "二等软座", "9": "商务座"}
	for train_data_str in train_data_str_list:
		tmp = train_data_str.split('|')
		train_no = tmp[2]
		to_station_telecode = tmp[7]
		has_tickets = tmp[11]
		for from_station_in_ticket, v in train_data.items():
			if v["telecode"] == to_station_telecode:
				to_station = from_station_in_ticket
				break
		if has_tickets == 'Y':
			train_number = tmp[3]
			start_time = tmp[8]
			end_time = tmp[9]
			duration_time = tmp[10]
			ticket_stock_and_price = tmp[39]
			print(
				'车次: {}, 票面出发站: {}, 票面到达站: {}, 实际到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
					train_number, from_station, to_station, to_station, start_time, end_time, duration_time))
			for i in range(0, len(ticket_stock_and_price), 10):
				t = ticket_stock_and_price[i:i + 10]
				if t[7:] != '000':
					print(seat_type[t[0]], end='')
					if t[6] == '3':
						print('(无座)', end='')
					print('\t￥' + t[1:5] + '.' + t[5] + '\t余票', end='')
					print(t[7:] + '张')
			continue
		datas_station_name = get_datas_station_name(headers, cookies, max_retries, sleep_time, train_no, from_station_telecode, to_station_telecode, depart_date)
		if not len(datas_station_name):
			continue
		station_names = []
		from_station_ind = -1
		for data_station_name in datas_station_name:
			if data_station_name['station_name'] == from_station:
				from_station_ind = len(station_names)
			station_names.append(data_station_name['station_name'])
		for from_ind in range(from_station_ind + 1):
			if station_names[from_ind] not in possible_train_datas:
				possible_train_datas[station_names[from_ind]] = {}
			for to_ind in range(from_station_ind + 1, len(station_names)):
				if station_names[to_ind] == '汕  头':  # 就你汕头搞特殊，害我出bug！
					station_names[to_ind] = '汕头'
				if station_names[to_ind] not in possible_train_datas[station_names[from_ind]]:
					possible_train_datas[station_names[from_ind]][station_names[to_ind]] = {}
				if train_no not in possible_train_datas[station_names[from_ind]][station_names[to_ind]]:
					possible_train_datas[station_names[from_ind]][station_names[to_ind]][train_no] = []
				possible_train_datas[station_names[from_ind]][station_names[to_ind]][train_no].append(
					to_station)
	for from_station_in_ticket, v in possible_train_datas.items():
		from_station_in_ticket_telecode = train_data[from_station_in_ticket]['telecode']
		for to_station_in_ticket, vv in v.items():
			to_station_in_ticket_telecode = train_data[to_station_in_ticket]['telecode']
			train_data_str_list = get_train_data_str_list(headers, cookies, max_retries, sleep_time, depart_date, from_station_in_ticket_telecode, to_station_in_ticket_telecode)
			if not len(train_data_str_list):
				continue
			for data_query_g_tmp in train_data_str_list:
				tmp = data_query_g_tmp.split('|')
				train_no = tmp[2]
				to_station_telecode = tmp[7]
				has_tickets = tmp[11]
				if train_no not in vv or to_station_telecode != to_station_in_ticket_telecode or has_tickets == 'N':
					continue
				train_number = tmp[3]
				start_time = tmp[8]
				end_time = tmp[9]
				duration_time = tmp[10]
				ticket_stock_and_price = tmp[39]
				print(
					'车次: {}, 票面出发站: {}, 票面到达站: {}, 实际到达站: {}, 出发时间: {}, 到达时间: {}, 历时: {}'.format(
						train_number, from_station_in_ticket, to_station_in_ticket, vv[train_no], start_time, end_time,
						duration_time))
				for i in range(0, len(ticket_stock_and_price), 10):
					t = ticket_stock_and_price[i:i + 10]
					if t[7:] != '000':
						print(seat_type[t[0]], end='')
						if t[6] == '3':
							print('(无座)', end='')
						print('\t￥' + t[1:5] + '.' + t[5] + '\t余票', end='')
						print(t[7:] + '张')
