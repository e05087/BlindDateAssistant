# -*- coding: utf-8 -*-
import json
import datetime
from bs4 import BeautifulSoup
import requests
import random
from math import sin, cos, sqrt, atan2, radians


def calculateDistance(slat,slng,dlat,dlng):	
	# approximate radius of earth in km
	R = 6373.0

	lat1 = radians(slat)
	lon1 = radians(slng)
	lat2 = radians(dlat)
	lon2 = radians(dlng)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = R * c * 1000 # m 

	return distance

def lcs(A, B):

	d = []
	for i in range(0,len(A)):
		d.append([])
		for j in range(0,len(B)):
			d[i].append(0)
	for i in range(0,len(B)):
		if B[i] == A[0]:
			d[0][i] = 1
		if i > 0:
			d[0][i] = max(d[0][i],d[0][i-1])
	for i in range(0,len(A)):
		if A[i] == B[0]:
			d[i][0] = 1
		if i > 0:
			d[i][0] = max(d[i][0],d[i-1][0])
 
	ret = 0
	for i in range(1,len(A)):
		for j in range(1,len(B)):
			if A[i] == B[j]:
				d[i][j] = max(d[i][j], d[i-1][j-1]+1)
			d[i][j] = max(d[i][j], d[i][j-1])
			d[i][j] = max(d[i][j], d[i-1][j])
			ret = max(ret, d[i][j])
	return ret

def getNearTheater(lat,lng,distance):
	'''
	return은 {cgv : [], lc: [], mb: []}
	'''
	returndic = {'cgv':[], 'lc':[], 'mb': []}
	cgv = json.load(open('cgvTheaterList.json',encoding='utf8'))
	lc = json.load(open('LotteCinemaTheaterList.json',encoding='utf8'))
	mb = json.load(open('MegaBoxTheaterList.json',encoding='utf8'))
	
	for i in cgv:
		if cgv[i][1] =='' or cgv[i][2] == '':
			continue
		dlat = float(cgv[i][1])
		dlng = float(cgv[i][2])
		if calculateDistance(lat,lng,dlat,dlng)<distance:
			returndic['cgv'].append((i,cgv[i][0]))
	for i in lc:
		if lc[i][1] =='' or lc[i][2] == '':
			continue
		dlat = float(lc[i][1])
		dlng = float(lc[i][2])
		if calculateDistance(lat,lng,dlat,dlng)<distance:
			returndic['lc'].append((i,lc[i][0]))
	for i in mb:
		if mb[i][1] =='' or mb[i][2] == '':
			continue
		dlat = float(mb[i][1])
		dlng = float(mb[i][2])
		if calculateDistance(lat,lng,dlat,dlng)<distance:
			returndic['mb'].append((i,mb[i][0]))
	return returndic
def timeTominute(time):
	time = time.split(':')
	hour = int(time[0])
	minute = int(time[1])
	return hour * 60 + minute
def minuteTotime(minute):
	return str(minute//60) + ':' + str(minute%60)
def getMovieList(theaterDic,date):
	'''
	theater 목록을 받아서 상영 영화와 시간을 return
	return 형태는 {영화제목 : {movieGenre: 영화장르, movieRuntime: 영화런타임, timetable : [(영화시간, 남은좌석수,영화관이름)]} ... }
	'''
	movieList = {}
	sort_on   = lambda pos:     lambda x: x[pos]
	# cgv 부터 시작.
	for i in theaterDic['cgv']:
		API_ENDPOINT = "http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?theatercode=" + str(i[0])+"&date=" + str(date.replace('-',''))
		# sending post request and saving response as response object
		r = requests.get(url = API_ENDPOINT)
		# extracting response text 
		pastebin_url = r.text
		result = BeautifulSoup(pastebin_url, 'html.parser')
		movies =  result.findAll("div", { "class" : "col-times" })
		for movie in movies:
			movie_info = movie.find("div", { "class" : "info-movie" })
			movie_name = str.strip(movie.find("strong").text)
			if movie_name is None:
				continue
			
			movie_info_detail =  movie.findAll("i")
			movie_genre = str.strip(movie_info_detail[0].text)
			movie_runtime = str.strip(movie_info_detail[1].text.replace('분',''))
			if movie_name not in movieList:
				movieList[movie_name] = {'movieGenre': movie_genre, 'movieRuntime': movie_runtime, 'timetable' : []}
			timetables= movie.findAll("div", { "class" : "info-timetable" })
			for time in timetables:
				timecolumn = time.findAll("li")
				for oneTime in timecolumn:
					s = oneTime.text
					s=''.join(i for i in s if i.isdigit())
					if len(s)>4: # 4미만인 경우 잔여좌석이 없거나 시간이 지남.
						movie_start_time = str(s[0:2])+':'+str(s[2:4])
						movie_remain_seat = s[4:]
						movieList[movie_name]['timetable'].append([movie_start_time, movie_remain_seat, i[1]])
		
	
	for i in theaterDic['lc']:
		API_ENDPOINT = "http://www.lottecinema.co.kr/LCWS/Ticketing/TicketingData.aspx"
		data = {"paramList":json.dumps({"MethodName":"GetPlaySequence","channelType":"HO",
		"osType":"Chrome","osVersion":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
		"playDate":str(date),"cinemaID":"1|1|"+str(i[0]),"representationMovieCode":""})}
		lcdata = {}
		# sending post request and saving response as response object
		r = requests.post(url = API_ENDPOINT, data = data)
		# extracting response text 
		pastebin_url = r.text
		lcJson = json.loads(pastebin_url)
		lcmovies = lcJson['PlaySeqsHeader']['Items']
		for movie in lcmovies:
			movieNumber = movie['MovieCode']
			movieName = movie['MovieNameKR']
			if movieNumber not in lcdata:
				lcdata[movieNumber] = movieName
		lcmovieplay = lcJson['PlaySeqs']['Items']
		for play in lcmovieplay:
			movie_remain_seat = play['BookingSeatCount']
			movie_name = lcdata[play['MovieCode']]
			movie_start_time =  play['StartTime']
			movie_end_time = play['EndTime']
			movie_runtime = timeTominute(movie_end_time) - timeTominute(movie_start_time)
			if movie_name not in movieList:
				movieList[movie_name] = {'movieGenre': '', 'movieRuntime': movie_runtime, 'timetable' : []}
			movieList[movie_name]['timetable'].append([movie_start_time, movie_remain_seat, str(i[1]) + ' 롯데시네마'])
			
	for i in theaterDic['mb']:
		API_ENDPOINT = "http://www.megabox.co.kr/pages/theater/Theater_Schedule.jsp"
		data={"cinema": i[0], "playdate": date}
		# sending post request and saving response as response object
		r = requests.post(url = API_ENDPOINT, data = data)
		# extracting response text 
		pastebin_url = r.text
		result = BeautifulSoup(pastebin_url, 'html.parser')
		movies =  result.findAll("tr", { "class" : "lineheight_80" })
		for movie in movies:
			movie_name = str.strip(movie.find('th',{'class':'title'}).find('strong').text)
			if len(movie_name) ==0:
				continue
			playlist = movie.findAll("div", { "class" : "cinema_time" })
			for play in playlist:
				hover_time = str.strip(play.find('span',{ "class" : "hover_time" }).text)
				movie_start_time = hover_time.split('~')[0]
				movie_end_time = hover_time.split('~')[1]
				movie_runtime = timeTominute(movie_end_time) - timeTominute(movie_start_time)
				movie_remain_seat = str.strip(play.find('span',{ "class" : "seat" }).text).split('/')[0]
				if movie_name not in movieList:
					movieList[movie_name] = {'movieGenre': '', 'movieRuntime': movie_runtime, 'timetable' : []}
				movieList[movie_name]['timetable'].append([movie_start_time, movie_remain_seat, str(i[1]) + ' 메가박스'])
			
		
	for i in movieList:
		movieList[i]['timetable'] = sorted(movieList[i]['timetable'], key=sort_on(0))
	
	return movieList
						
			
def getRecommendedRestaurant(lat,lng,opt):
	'''
	opt가 0이면 소개팅, 1이면 카페, 2이면 술집
	'''
	
	if opt == 0:
		search_query = "%EC%86%8C%EA%B0%9C%ED%8C%85"
	elif opt == 1:
		search_query = "%EC%B9%B4%ED%8E%98"
	elif opt == 2:
		search_query = "%EC%88%A0%EC%A7%91"
	
	API_ENDPOINT = "https://www.diningcode.com/list.php?query="+search_query+"&lat="+str(lat)+"&lng="+str(lng)
	
	# sending post request and saving response as response object
	r = requests.get(url = API_ENDPOINT)
	 
	# extracting response text 
	pastebin_url = r.text
	soup = BeautifulSoup(pastebin_url, 'html.parser')
	
	restaurantDic = {}
	for result in soup.findAll("dc-restaurant"):
		restaurantName = str.strip(result.find("div", { "class" : "dc-restaurant-name" }).text)
		restaurantCategory = str.strip(result.find("div", { "class" : "dc-restaurant-category" }).text)
		info =  result.findAll("div", { "class" : "dc-restaurant-info-text" })
		restaurantDescription =str.strip(info[0].text)
		restaurantLoc = str.strip(info[1].text)
		restaurantNum = str.strip(info[2].text)
		if restaurantName not in restaurantDic:
			restaurantDic[restaurantName] = {"category": restaurantCategory, "description": restaurantDescription
			,"location" : restaurantLoc,"number" : restaurantNum}
	
	return restaurantDic

def restaurantSelect(lat,lng,opt):
	restaurant = getRecommendedRestaurant(lat,lng,opt)
	if opt ==0:
		ment = '레스토랑'
	if opt ==1:
		ment = '카페'
	if opt ==2:
		ment = '술집'
	restaurantlist = []
	for ii,i in enumerate(restaurant):
		#print(restaurant[i])
		restaurantlist.append((i,restaurant[i]['location']))
		print(str(ii+1).ljust(5),str(i).ljust(25),str(restaurant[i]['category']).ljust(30),str(restaurant[i]['description']).ljust(30))
	selected_restaurant_index = -1
	print('------------------------------------------------------------')
	while selected_restaurant_index<0:
		print('추천 ' + ment + '목록입니다. 번호를 골라주세요.\n')
		try:
			selected_restaurant_index = int(input('추천을 받으시려면 0을 눌러주세요.'))
			if selected_restaurant_index > len(restaurant):
				selected_restaurant_index = -1
				print('오류가 발생했습니다. 다시골라주세요.\n')
		except:
			print('오류가 발생했습니다. 다시골라주세요.\n')
			selected_restaurant_index = -1
	if selected_restaurant_index ==0:
		selected_restaurant_index = random.randint(1,len(restaurant))
	selected_restaurant_name = restaurantlist[selected_restaurant_index-1][0]
	selected_restaurant_loc = restaurantlist[selected_restaurant_index-1][1]
	return selected_restaurant_name, selected_restaurant_loc
	
def movieSelect(lat,lng,date,time,distance):
	'''
	time 은 xx:xx~xx:xx 로 이 시간 사이에 있는 영화들만 골라서 보여준다.
	'''
	a = getNearTheater(lat,lng,distance)
	b = getMovieList(a,date)
	#print(b)
	starttime = time.split('~')[0]
	endtime = time.split('~')[1]
	select_movie_list = []
	movies_time_table = {}
	for i in b:
		for iindex,ii in enumerate(b[i]['timetable']):
			if timeTominute(ii[0]) >= timeTominute(starttime) and timeTominute(ii[0]) <= timeTominute(endtime) : # 데이트 시간 이전의 영화 제외
				if i not in select_movie_list:
					select_movie_list.append(i)
				if i not in movies_time_table:
					movies_time_table[i] = []
				movies_time_table[i].append((ii[0],ii[1],ii[2]))
					

	for ii,i in enumerate(select_movie_list):
		print(ii+1, i)
	selected_movie_index = -1
	
	movie_select_flag = False
	while not movie_select_flag:
		while selected_movie_index<0:
			try:
				selected_movie_index = int(input('\n원하는 영화의 번호를 입력해주세요. 딱히 선호하는 영화가 없다면 0을 입력해주세요: '))
			except:
				selected_movie_index = -1
			if selected_movie_index > len(select_movie_list) and selected_movie_index != 0:
				selected_movie_index = -1

		if selected_movie_index == 0: # 딱히 선호하는 영화가 없을때
			selected_movie_name = random.choice(select_movie_list)
		else:
			selected_movie_name = select_movie_list[selected_movie_index-1]
		
		selected_movie_timetable = movies_time_table[selected_movie_name]
		try:
			if len(selected_movie_timetable) == 0:
				print('죄송합니다. 선택하신 영화가 맞는 시간이 없네요. 다른 영화를 골라주세요.\n')
				movie_select_flag = False
			else:
				movie_select_flag = True
				
		except:
			print('죄송합니다. 선택하신 영화가 맞는 시간이 없네요. 다른 영화를 골라주세요.\n')
			movie_select_flag = False
		
	print('Num'.ljust(6),'StartTime'.ljust(10), 'RemainSeat'.ljust(12), 'TheaterName'.ljust(12))
	for ii,i in enumerate(selected_movie_timetable):
		print(str(ii+1).ljust(6), str(i[0]).ljust(10),str(i[1]).ljust(12),str(i[2]).ljust(12))
	
	selected_movie_time_index = -1
	while selected_movie_time_index<0:
		try:
			print('\n선택하신 '+ selected_movie_name + '의 상영관과 상영시간은 위와 같습니다. 번호를 골라주세요.\n')
			selected_movie_time_index = int(input('선호하는 시간이 없다면 0을 입력해주세요: '))
		except:
			selected_movie_time_index = -1
	selected_movie_time = selected_movie_timetable[selected_movie_time_index-1][0]
	selected_theater_name = selected_movie_timetable[selected_movie_time_index-1][2]
	
	return selected_movie_time,selected_movie_name,selected_theater_name

def printopts():
	print('------------------------------------------------------------')
	print(1, '식사')
	print(2, '영화')
	print(3, '카페')
	print(4, '술')
	print(5, '일정 종료')
	print('------------------------------------------------------------')
	selected_opt = -1
	while selected_opt<0:
		try:
			selected_opt = int(input('무엇을 하시겠어요? 번호를 눌러주세요. 추천을 받으시려면 0을 눌러주세요: ')) 
			print('------------------------------------------------------------')
			print('\n')
			if selected_opt >5:
				selected_opt = -1
		except:
			selected_opt = -1
	return selected_opt
def decideWhichAction(nowtime,beforeOPT):
	# 만나는시간이 11시 이전, 2시~4시 일경우 영화 보고 밥
	# 만나는시간이 8시 이후일 경우 술만
	# 만나는시간이 11시~2시 일경우 밥먹고 영화
	# 만나는 시간이 4시~8시일경우 밥먹고 영화
	# beforeOPT 가 0 이면 첫 행동, 1이면 이전에 밥, 2이면 이전에 영화, 3이면 이전에 카페, 4이면 이전에 술
	if beforeOPT==0:
		firstment =  '에 두근두근 첫 만남을 하시는군요! '
	elif beforeOPT==1:
		firstment =  '에 식사를 마치실거에요!'
	elif beforeOPT==2:
		firstment =  '에 영화가 끝날거에요!'
	elif beforeOPT==3:
		firstment =  '에 커피 한잔을 마칠거에요!'
	elif beforeOPT==4:
		firstment =  '에 술 한잔씩 하셨을거에요!'
	print('\n'+str(nowtime) + firstment)
	print('이제 무엇을 하실래요?\n')
	if timeTominute(str(nowtime)) < timeTominute('11:00'):
		if beforeOPT==3:
			print('그 시간대면 영화를 보러 가시는 것을 추천합니다.')
		else:
			print('그 시간대면 카페에 가시는 것을 추천합니다.')
		selected_opt = printopts()
		if selected_opt ==0:
			if beforeOPT == 3:
				selected_opt = 2
			else:
				selected_opt = 3
	elif timeTominute(str(nowtime)) >= timeTominute('11:00') and timeTominute(str(nowtime)) <= timeTominute('14:00'):
		if beforeOPT==1:
			print('그 시간대면 카페에 가시는 것을 추천합니다.')
		else:
			print('그 시간대면 식사를 하시는 것을 추천합니다.')
		selected_opt = printopts()
		if selected_opt ==0:
			if beforeOPT == 1:
				selected_opt = 3
			else:
				selected_opt = 1
	elif timeTominute(str(nowtime)) >= timeTominute('14:00') and timeTominute(str(nowtime)) <= timeTominute('16:00'):
		if beforeOPT==2:
			print('그 시간대면 카페에 가시는 것을 추천합니다.')
		else:
			print('그 시간대면 영화를 보시는 것을 추천합니다.')
		selected_opt = printopts()
		if selected_opt ==0:
			if beforeOPT == 2:
				selected_opt = 3
			else:
				selected_opt = 2
	elif timeTominute(str(nowtime)) >= timeTominute('16:00') and timeTominute(str(nowtime)) <= timeTominute('20:00'):
		if beforeOPT==1:
			print('그 시간대면 카페에 가시는 것을 추천합니다.')
		else:
			print('그 시간대면 식사를 하시는 것을 추천합니다.')
		selected_opt = printopts()
		if selected_opt ==0:
			if beforeOPT == 1:
				selected_opt = 3
			else:
				selected_opt = 1
	elif timeTominute(str(nowtime)) >= timeTominute('20:00'):
		if beforeOPT==4:
			print('그 시간대면 카페에 가시는 것을 추천합니다.')
		else:
			print('그 시간대면 술 한잔 하시는 것을 추천합니다.')
		selected_opt = printopts()
		if selected_opt ==0:
			if beforeOPT == 4:
				selected_opt = 3
			else:
				selected_opt = 4
			
	if selected_opt == 1:
		aftertime = timeTominute(str(nowtime)) + 90
	elif selected_opt == 2:
		aftertime = timeTominute(str(nowtime)) + 130
	elif selected_opt == 3:
		aftertime = timeTominute(str(nowtime)) + 120
	elif selected_opt == 4:
		aftertime = timeTominute(str(nowtime)) + 120
	else:
		aftertime = timeTominute(str(nowtime))
	
	return selected_opt, minuteTotime(aftertime)
def main():
	
	print('마, 소개팅 스케쥴러 프로그램입니다. \n')
	checkRightFlag = False
	while not checkRightFlag:
		subway_pass_flag = False
		while not subway_pass_flag:
			print('--------------------------------------------------------------')
			input_subway = input('소개팅 약속장소 근처 지하철 역을 한글로 입력해주세요: ')
			if len(input_subway) !=0:
				subway_pass_flag = True

		subway = json.load(open('subway.json',encoding='utf8'))
		lcs_nearst_value = []
		lcs_nearst_name = []
		lcs_nearst_lat = []
		lcs_nearst_lng = []
		for i in subway:
			lcsvalue = lcs(input_subway,str(i))/min(len(input_subway),len(str(i)))
			#lcsvalue = lcs(input_subway,str(i))
			if lcsvalue>0.5:
				lcs_nearst_value.append(lcsvalue)
				lcs_nearst_name.append(str(i))
				lcs_nearst_lat.append(float(subway[i][0]))
				lcs_nearst_lng.append(float(subway[i][1]))
		
		if len(lcs_nearst_value) ==0:
			checkRightFlag = False
			subway_pass_flag = False
			print('\n입력하신 지하철역이 DB에 존재하지 않습니다. 다른 역을 입력해주세요.\n')
			continue
		for zz,z in enumerate(lcs_nearst_name):
			print(zz+1,z)
		print('\n가(이) DB에 탐지 되었습니다.')
		try:
			select_subway = int(input('이 중 맞는 것의 번호를 입력해주세요. 없으면 0을 눌러주세요: '))
		except:
			checkRightFlag = False
			subway_pass_flag = False
			print('오류가 발생했습니다. 다시 입력해주세요.')
		if select_subway == 0:
			checkRightFlag = False
			subway_pass_flag = False
			print('\n입력하신 지하철역이 DB에 존재하지 않습니다. 다른 역을 입력해주세요.\n')
		elif select_subway>0 and select_subway <= len(lcs_nearst_name):
			checkRightFlag = True
		else:
			checkRightFlag = False
			subway_pass_flag = False
			print('\n입력하신 지하철역이 DB에 존재하지 않습니다. 다른 역을 입력해주세요.\n')
		
	lcs_index = select_subway-1
	
	my_subway = lcs_nearst_name[lcs_index]
	my_lat = lcs_nearst_lat[lcs_index]
	my_lng = lcs_nearst_lng[lcs_index]
	print(my_subway + '역, 위경도는 ',my_lat,my_lng)
	
	timeFlag = False
	while not timeFlag:
		try:
			print('\n 소개팅 예정 날짜와 시간을 말해주세요. 예를들어 2017년 11월 27일 오후 6시일 경우, 2017-11-27 18:00 와 같이 입력해주세요.')
			meetingtime = input('입력: ')
			myDatetime = datetime.datetime.strptime(meetingtime, '%Y-%m-%d %H:%M')
			if myDatetime < datetime.datetime.now():
				timeFlag = False
				print('소개팅은 미래에 하는 것이에요..')
			else:
				myDatetime_date = myDatetime.strftime('%Y-%m-%d')
				myDatetime_date_format = myDatetime.strftime('%Y%m%d')
				myDatetime_time = myDatetime.strftime('%H:%M')
				timeFlag = True
				print('-------------------------------------\n')
				#print(lunchtime>myDatetime,dinnertime>myDatetime)
		except:
			print('다시 입력해주세요.\n')
				
	selected_opt = 0
	date = myDatetime_date
	nowtime = myDatetime_time
	lat = my_lat
	lng = my_lng
	distance = 1500
	plan = []
	while selected_opt !=5:
		selected_opt,aftertime = decideWhichAction(nowtime,selected_opt)
		
		if selected_opt == 1:
			rname, rloc = restaurantSelect(lat,lng,0)
			print('\n')
			print(rname + '에서 식사를 하시겠네요. ' + rname + '의 위치는 '+ rloc + '입니다.')
			plan.append([nowtime, rname, '식사',selected_opt])
		if selected_opt == 3:
			rname, rloc = restaurantSelect(lat,lng,1)
			print('\n')
			print(rname + '에서 커피를 마시겠네요. ' + rname + '의 위치는 '+ rloc + '입니다.')
			plan.append([nowtime, rname, '커피',selected_opt])
		if selected_opt == 4:
			rname, rloc = restaurantSelect(lat,lng,2)
			print('\n')
			print(rname + '에서 술을 마시겠네요. ' + rname + '의 위치는 '+ rloc + '입니다.')
			plan.append([nowtime, rname, '술',selected_opt])
		if selected_opt == 2:
			movietime = nowtime + '~' + minuteTotime(timeTominute(nowtime) + 90)
			print(movietime + ' 의 영화를 탐색하겠습니다.')
			mtime, mname,tname = movieSelect(lat,lng,date,movietime,distance)
			print('\n')
			print(tname + '에서 ' +mtime+'에 '+ mname + ' 을 보시겠네요.') 
			plan.append([mtime, tname, mname,selected_opt])
		nowtime = aftertime
	print('\n소개팅 계획이 완성되었습니다!\n')
	for oneplan in plan:
		if oneplan[3] == 2: # 영화감상
			print(oneplan[0] + '에 ' + oneplan[1] + '에서 ' + oneplan[2] + ' 감상 예정')
		else: # 영화감상
			print(oneplan[0] + '에 ' + oneplan[1] + '에서 ' + oneplan[2] + ' 예정')
	print('\n행운을 빌게요')
		
		
		
		
		#if skipFoodflag == 1 or skipFoodflag == 0:

#print(getRecommendedRestaurant(37.5552902398991,126.936342959767,0))
#print(movieSelect(37.5552902398991,126.936342959767,'2017-11-29','13:00~17:00',1500))


main()