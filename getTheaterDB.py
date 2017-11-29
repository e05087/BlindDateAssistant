# importing the requests library
import requests
import re
import json
from tqdm import tqdm
from bs4 import BeautifulSoup

def save(newarray,filename):
	with open(filename, 'w',encoding='utf8') as outfile:
		json.dump(newarray, outfile, ensure_ascii = False)

def getCGV():
	'''
	CGV 영화관 정보 수집 후 저장
	'''
	print("CGV 영화관 탐지를 시작합니다.")
	# defining the api-endpoint 
	API_ENDPOINT = "http://www.cgv.co.kr/theaters"
	 
	# sending post request and saving response as response object
	r = requests.get(url = API_ENDPOINT)
	 
	# extracting response text 
	pastebin_url = r.text
	t1Loc = [m.end() for m in re.finditer('theaterJsonData = ', pastebin_url)]
	areaListString = ''
	tempindex = t1Loc[0]
	while True:
		if pastebin_url[tempindex] == ';':
			break
		tempindex = tempindex + 1
		areaListString = areaListString + pastebin_url[tempindex-1]
	areaList = json.loads(areaListString)

	theaterCodes = {}
	for i in areaList:
		for ii in i['AreaTheaterDetailList']:
			if ii['TheaterCode'] not in theaterCodes:
				theaterCodes[ii['TheaterCode']] =[]
				theaterCodes[ii['TheaterCode']].append(ii['TheaterName'])

	print(str(len(theaterCodes)) + '개의 CGV 영화관이 탐지 되었습니다.')
	a = 0
	for i in tqdm(theaterCodes):
		# defining the api-endpoint 
		API_ENDPOINT = "http://www.cgv.co.kr/theaters/?page=location&theaterCode="+str(i)+"#menu"
		 
		# sending post request and saving response as response object
		r = requests.get(url = API_ENDPOINT)
		
		pastebin_url = r.text
		t1Loc = [m.end() for m in re.finditer('locationTheaterJsonData = ', pastebin_url)]
		locationStr = ''
		tempindex = t1Loc[0]
		while True:
			if pastebin_url[tempindex] == ';':
				break
			tempindex = tempindex + 1
			locationStr = locationStr + pastebin_url[tempindex-1]
		location = json.loads(locationStr)

		for thisLoc in location:
			if thisLoc['code'] == i:
				theaterCodes[i].append(thisLoc['lat'])
				theaterCodes[i].append(thisLoc['lng'])
				a= a+1
				break
	print(str(a) + '개의 CGV 영화관의 위치를 탐지 했습니다.')

	save(theaterCodes,'cgvTheaterList.json')
	
def getLotteCinema():
	print("롯데시네마 영화관 탐지를 시작합니다.")
	detailList = [1,2,3,4,5,6,7,101]
	theaterCodes = {}
	a = 0
	for i in tqdm(detailList):
		API_ENDPOINT = "http://www.lottecinema.co.kr/LCWS/Cinema/CinemaData.aspx"
		data = {"paramList":json.dumps({"MethodName":"GetCinemaByArea","channelType":"HO","osType":"Chrome",
		"osVersion":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
		"multiLanguageID":"KR","divisionCode":"1","detailDivisionCode":str(i)}, separators=(',',':'))}
		# sending post request and saving response as response object
		r = requests.post(url = API_ENDPOINT,data = data)
		 
		# extracting response text 
		pastebin_url = r.text
		theaterList = json.loads(pastebin_url)
		for ii in theaterList['Cinemas']['Items']:
			if ii['CinemaID'] not in theaterCodes:
				API_ENDPOINT = "http://www.lottecinema.co.kr/LCWS/Cinema/CinemaData.aspx"
				data = {"paramList":json.dumps({"MethodName":"GetCinemaDetailItem","channelType":"HO",
				"osType":"Chrome","osVersion":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
				"divisionCode":"1","detailDivisionCode":str(i),"cinemaID":str(ii['CinemaID']),"memberOnNo":0}, separators=(',',':'))}
				# sending post request and saving response as response object
				r = requests.post(url = API_ENDPOINT,data = data)
				 
				# extracting response text 
				pastebin_url = r.text
				theaterInfo = json.loads(pastebin_url)
				theaterCodes[ii['CinemaID']] = []
				theaterCodes[ii['CinemaID']].append(ii['CinemaName'])
				theaterCodes[ii['CinemaID']].append(theaterInfo['CinemaDetail']['Latitude'])
				theaterCodes[ii['CinemaID']].append(theaterInfo['CinemaDetail']['Longitude'])
				a = a+1

	print(str(a) + '개의 롯데시네마 영화관의 위치를 탐지 했습니다.')
	save(theaterCodes,'LotteCinemaTheaterList.json')


def getMegaBox():
	print("메가박스 영화관 탐지를 시작합니다.")
	regionList = [10,30,35,45,55,65,70,80]
	theaterCodes = {}
	a = 0
	for i in tqdm(regionList):
		API_ENDPOINT = "http://www.megabox.co.kr/DataProvider"
		data = {"_command" : "Cinema.getCinemasInRegion",
		"siteCode":36,
		"areaGroupCode":i,
		"reservationYn":"N"}
		# sending post request and saving response as response object
		r = requests.post(url = API_ENDPOINT,data = data)
		 
		# extracting response text 
		pastebin_url = r.text
		theaterList = json.loads(pastebin_url)

		for ii in theaterList['cinemaList']:
			cinemaCode = ii['cinemaCode']
			cinemaName = ii['cinemaName']
			API_ENDPOINT = "http://www.megabox.co.kr/?menuId=theater-detail&region=" +str(i)+"&cinema=" +str(cinemaCode)+"#menu3"

			# sending post request and saving response as response object
			r = requests.get(url = API_ENDPOINT)
			 
			# extracting response text 
			pastebin_url = r.text
			t1Loc = [m.end() for m in re.finditer('new naver.maps.LatLng', pastebin_url)]
			locStr = ''
			tempindex = t1Loc[0]
			while True:
				if pastebin_url[tempindex] == ';':
					break
				tempindex = tempindex + 1
				locStr = locStr + pastebin_url[tempindex-1]
			latlngList = locStr.replace(' ','').replace('(','').replace(')','').split(',')
			if cinemaCode not in theaterCodes:
				theaterCodes[cinemaCode] = []
				theaterCodes[cinemaCode].append(cinemaName)
				theaterCodes[cinemaCode].append(float(latlngList[0]))
				theaterCodes[cinemaCode].append(float(latlngList[1]))
				a = a+1
				
	print(str(a) + '개의 메가박스 영화관의 위치를 탐지 했습니다.')
	save(theaterCodes,'MegaBoxTheaterList.json')


getCGV()
getLotteCinema()
getMegaBox()
