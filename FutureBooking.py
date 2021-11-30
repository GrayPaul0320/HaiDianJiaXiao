# *_*coding:utf-8 *_*
import requests
import json
import hashlib
from configparser import ConfigParser
import sys
from datetime import datetime, timedelta
import pickle
import urllib.parse as urlparse
from urllib.parse import urlencode
import pandas as pd
import time
import os
class YueChe():
	def __init__(self):
		self.cfg = ConfigParser()
		self.cfg.read("config.ini")
		self.cookie = ""
		self.username = self.cfg.get("userinfo", "phone_num")
		self.password = hashlib.md5(self.cfg.get("userinfo", "password").encode("utf-8")).hexdigest()
		self.title = ""
		self.message = ""
		self.booking_list = ''
		self.tasks = pd.read_csv("./tasks.csv", sep=",")
		self.tasks["date"] = pd.to_datetime(self.tasks["date"]).dt.date
		

	def SendMessageToWechat(self):
		url = "https://sctapi.ftqq.com/" + self.cfg.get("server_chan_api", "sendkey") + ".send"
		paras = {"title": self.title,
				 "desp": self.message}
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)
		requests.post(url=urlparse.urlunparse(url_parts))


	def LogInXueCheBu(self, ):
		headers = {"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;"}
		# print(json.dumps({"username": self.username, "passwordmd5": self.password}))
		request = requests.post(url=self.cfg.get("url", "log_in_xuechebu"),
								params={"username": self.username, "passwordmd5": self.password},
								headers=headers)
		self.cookies = requests.utils.dict_from_cookiejar(request.cookies)
		self.cfg.set("userinfo", "jgid", json.loads(request.text)["data"]["JGID"])
		self.cfg.set("userinfo", "xybh", json.loads(request.text)["data"]["XYBH"])
		self.cfg.set("userinfo", "id", json.loads(request.text)["data"]["ID"])
		self.cfg.set("userinfo", "xxzh", json.loads(request.text)["data"]["XXZH"])
		self.cfg.write(sys.stdout)
		if json.loads(request.text)["code"] == 0:
			self.title = "登陆成功" + str(json.loads(request.text)["code"])
			self.message = json.loads(request.text)["message"]
			self.SendMessageToWechat()
		else:
			self.title = "ERROR" + str(json.loads(request.text)["code"])
			self.message = json.loads(request.text)["message"]
			self.SendMessageToWechat()
			sys.exit(0)
		return

	def GetStudentXxjd(self):
		headers = {
			"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
			"Host": "xcbapi.xuechebu.com",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		paras = {"ipaddress": "192.168.1.107",
				 "ossdk": "29",
				 "os": "an",
				 "imei": "4c432414d2f97df0unknownHUAWEIVOG-AL00",
				 "appversion": "5.2.5",
				 "osversion": "10",
				 "userid": self.cfg.get("userinfo", "id"),
				 "version": "5.2.5"}
		url = self.cfg.get("url", "student_xxjd")
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)

		request = requests.get(url=urlparse.urlunparse(url_parts), cookies=self.cookies, headers=headers)

		return

	def SetBadingStuInfo(self):
		headers = {
			"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
			"Host": "haijia.xuechebu.com:8008",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		paras = {"password": self.cfg.get("userinfo", "password"), "jgid": self.cfg.get("userinfo", "jgid"),
				 "xybh": self.cfg.get("userinfo", "xybh")}
		url = self.cfg.get("url", "log_in_haijia")
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)

		request = requests.get(url=urlparse.urlunparse(url_parts), cookies=self.cookies, headers=headers)
		self.cookies.update(requests.utils.dict_from_cookiejar(request.cookies))
		return

	def GetYysdList(self):
		"""
		Get all of the booking list information from now
		:return: a dataframe that conclude the reservation information
		"""
		headers = {
			"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
			"Host": "haijia.xuechebu.com:8008",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		paras = {"ipaddress": "192.168.1.107",
				 "ossdk": "29",
				 "os": "an",
				 "trainType": "2",
				 "xxzh": self.cfg.get("userinfo", "xxzh"),
				 "yyrq": datetime.now().strftime("%Y-%m-%d"),
				 "imei": "4c432414d2f97df0unknownHUAWEIVOG-AL00",
				 "appversion": "5.2.5",
				 "osversion": "10",
				 "xybh": self.cfg.get("userinfo", "xybh"),
				 "version": "5.2.5"}
		url = self.cfg.get("url", "get_yysd_list")
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)
		request = requests.get(url=urlparse.urlunparse(url_parts), cookies=self.cookies, headers=headers)
		# print(self.cookies)
		result = json.loads(request.text)
		if result["code"] == 0:
			# print("获取约车列表成功")
			self.booking_list = pd.DataFrame(result["data"])
			self.booking_list["date"] = pd.to_datetime(self.booking_list["Yyrq"]).dt.date
			self.booking_list[["Xnsd"]] = self.booking_list[["Xnsd"]].astype(int)
			# self.booking_list.to_csv("./ava.csv", index=None)
		else:
			self.title = "错误\t" + str(result["code"])
			self.message = result["message"]
			self.SendMessageToWechat()
			sys.exit(0)
		return self.booking_list

	def CIYyCars2(self, date, yysd):
		headers = {
			"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
			"Host": "haijia.xuechebu.com:8008",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		paras = {"ipaddress": "192.168.1.107",
				 "ossdk": "29",
				 "os": "an",
				 "filters[xnsd]": yysd,
				 "appversion": "5.2.5",
				 "filters[xxzh]": self.cfg.get("userinfo", "xxzh"),
				 "version": "5.2.5",
				 "filters[yyrq]": date,
				 "filters[SdType]": "",
				 "xxzh": self.cfg.get("userinfo", "xxzh"),
				 "filters[trainType]": "2",
				 "imei": "4c432414d2f97df0unknownHUAWEIVOG-AL00",
				 "osversion": "10",
				 "filters[IsXnsd]": "1"
				 }
		url = self.cfg.get("url", "CI_YyCars2")
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)
		request = requests.get(url=urlparse.urlunparse(url_parts), cookies=self.cookies, headers=headers)
		result = json.loads(request.text)
		if result["code"] == 0:
			avaliable_cars = pd.DataFrame(result["data"]["Result"])
			avaliable_cars_num = result["data"]["Total"]
		else:
			self.title = "错误\t" + str(result["code"])
			self.message = result["message"]
			self.SendMessageToWechat()
			sys.exit(0)
		return avaliable_cars, avaliable_cars_num

	def ClYyAddByMutil(self, carparam):
		"""
		Book a vehicle according to the specified parameters,
		while the parameters follow the format(02134.2021-11.17.2004.)
		:param 02134.2021-11.17.2004.(carnum.date.timecode.)
		:return: the Completed task if book successfully, otherwise code error
		"""
		headers = {
			"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
			"Host": "haijia.xuechebu.com:8008",
			"Connection": "Keep-Alive",
			"Accept-Encoding": "gzip"
		}
		paras = {"SdType": "",
				 "IsXnsd": "1",
				 "ipaddress": "192.168.1.107",
				 "ossdk": "29",
				 "os": "an",
				 "trainType": "2",
				 "params": carparam,
				 "version": "5.2.5",
				 "jlcbh": "",
				 "xxzh": self.cfg.get("userinfo", "xxzh"),
				 "isJcsdYyMode": "5",
				 "imei": "4c432414d2f97df0unknownHUAWEIVOG-AL00",
				 "osversion": "10",
				 }
		url = self.cfg.get("url", "ClYyAddByMutil")
		url_parts = list(urlparse.urlparse(url))
		query = dict(urlparse.parse_qsl(url_parts[4]))
		query.update(paras)
		url_parts[4] = urlencode(query)
		request = requests.get(url=urlparse.urlunparse(url_parts), cookies=self.cookies, headers=headers)
		result = json.loads(request.text)
		print(result)
		if result["code"] == 0:
			self.title = "约车成功"
			self.message = carparam.replace(".", "&&&")
			self.SendMessageToWechat()
		else:
			self.title = result["code"]
			self.message = result["message"]
			self.SendMessageToWechat()
		return result["code"]


	def Initial(self):
		self.LogInXueCheBu()
		self.GetStudentXxjd()
		self.SetBadingStuInfo()

# process the tasks one by one until all the tasks done
def AdjustTime():
	headers = {
		"User-Agent": "android_haijia;v5.2.5;phone:VOG-AL00:10;",
		"Host": "api.xuechebu.com",
		"Connection": "Keep-Alive",
		"Accept-Encoding": "gzip"
	}
	url = "http://api.xuechebu.com/Device/GetDeviceParameter"
	request = requests.get(url=url, headers=headers)
	server_time = datetime.strptime(request.headers["Date"], "%a, %d %b %Y %H:%M:%S %Z") + timedelta(hours=8)
	# (server_time.hour,server_time.minute,server_time.second)
	return (server_time.hour, server_time.minute, server_time.second)


if __name__ == "__main__":
	X = YueChe()
	carparams = []
	while True:
		now = datetime.now()
		if (7,34,45)<=(now.hour,now.minute,now.second)<=(7,34,50):
			break
		else:
			time.sleep(5)

	while True:
		if (7,35,0) >= AdjustTime() >= (7,34,50):
			X.Initial()
			booking_list = X.GetYysdList()
			avaliable_tasks = pd.merge(booking_list, X.tasks, on=["date", "Xnsd"])
			avaliable_tasks = avaliable_tasks[avaliable_tasks["SL"]>0]
			avaliable_tasks = avaliable_tasks.reset_index()
			avaliable_car_num = avaliable_tasks["SL"].sum()
			for indx in avaliable_tasks.index:
				avaliable_cars, _ = X.CIYyCars2(str(avaliable_tasks.at[indx, "date"]),
												str(avaliable_tasks.at[indx, "Xnsd"]))
				for selected_car in avaliable_cars["CNBH"].values:
					carparam = str(selected_car) + "." + str(avaliable_tasks.at[indx, "date"]) + "." + str(
						avaliable_tasks.at[indx, "Xnsd"]) + "."
					carparams.append(carparam)
			break
	while True:
		if AdjustTime() >= (7,35,0):
			break
	print(carparams)
	for carparam in carparams:
		result = X.ClYyAddByMutil(carparam)
		if result == 0:
			break
		else:
			continue

