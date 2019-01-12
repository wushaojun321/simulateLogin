# encoding:utf8
import requests
import pyquery
from pyv8 import PyV8
from PIL import Image

def encrypt(password, publicKey):
	with PyV8.JSContext() as ctxt:
		with open('rsa.js') as f:
			js = f.read()
		ctxt.locals.publicKey = publicKey
		ctxt.locals.password = password
		ctxt.eval(js)
		res = ctxt.locals.res
	return res

class LuLogin(object):
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.session = requests.session()
		self.headers = {
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
		}

	def get_data(self):
		url = "https://user.lu.com/user/login?returnPostURL=https%3A%2F%2Fwww.lu.com%2F"
		r = self.session.get(url, headers=self.headers)
		pq = pyquery.PyQuery(r.content)
		self.publicKey = pq("input#publicKey")[0].value
		self.deviceKey = pq("input#deviceKey")[0].value
		self.deviceInfo = pq("input#deviceInfo")[0].value

	def captcha(self):
		url = "https://user.lu.com/user/captcha/captcha.jpg?source=login&_=1547303278100"
		r = self.session.get(url, headers=self.headers)
		with open('captcha.png', "wb") as f:
			f.write(r.content)
		im = Image.open('captcha.png')
		im.show()
		self.code = raw_input('code: ')

	def run(self):
		self.get_data()
		self.encrypt_password = encrypt(self.password, self.publicKey)
		self.captcha()
		data = {
			"isTrust": "Y",
			"password": self.encrypt_password ,
			"openlbo": "1",
			"deviceKey": self.deviceKey,
			"deviceInfo": self.deviceInfo,
			"loginFlag": "1",
			"hIsOpenLboAccStatus": "0",
			"hIsSignLboUserCrsChecked": "0",
			"userName": self.username,
			"pwd": "************",
			"validNum": self.code,
			"signLoginAgreement": "on",
			"signLoginAgreementLbo": "on",
		}
		self.headers["X-Requested-With"] = "XMLHttpRequest"
		r = self.session.post("https://user.lu.com/user/login", headers=self.headers, data=data)
		print r.content

if __name__ == '__main__':
	lu = LuLogin("xxxxxxxx", "xxxxxxx")
	lu.run()

