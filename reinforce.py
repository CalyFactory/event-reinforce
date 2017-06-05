
#####
##TODO 
##1. 주변역찾아서 두번째 value로 값넣어주기.
##2. 다양한 testcase찾아보기.
##3. 성민이한테 텀겨줄데이터 세팅하기.
##4. 완성된데이터 db에 넣기.

from common import db_manager
from common.util import utils
from enum import Enum

reinforce_result = lambda state,data : {'code':state,'event_info_data':data}

class EventRecoStatusCode(Enum):

	#모든 데이터가 잘들어가있는경우. => 바로 리턴. 
	RECO_PERFECT = 1	

	#비추천일 경우.  => 
	#1.이벤트타입이 없어서. 
	#2.아예 비추천 항목일경우.		
	RECO_CANT = 2


	#위치가없고 이벤트타입이 있는경우.
	RECO_NO_LOCA_HAS_EVENTTYPE = 3	



class Reinforce:

	def __init__(self,event_info_data):
		self.__event_reco_status_code = EventRecoStatusCode.RECO_CANT  
		self.event_info_data = event_info_data	
		self.event_reco_result = reinforce_result(EventRecoStatusCode.RECO_CANT,self.event_info_data)							
		self.__checkRecoStauts()
		self.__reinForceForEventData()


	def __checkRecoStauts(self):
		# print(self.event_info_data["locations"])
		# print(self.event_info_data["event_types"] )
		# print(self.event_info_data["event_types"] != "None")
		# print(self.event_info_data["locations"] == "None")
		#모든데이터가 잘들어가 있는경우
		if self.event_info_data["locations"] != "None" and self.event_info_data["event_types"] != "None":
			self.__event_reco_status_code = EventRecoStatusCode.RECO_PERFECT  

		#location이 cannot일경우 데이터를 추천해 줄 수없다.
		#eventType이 None일경우 데이터를 추천해 줄 수 없다.
		elif self.event_info_data["locations"] == "Cannot" or  self.event_info_data["event_types"] == "None":		
			self.__event_reco_status_code = EventRecoStatusCode.RECO_CANT  


		#위치가없고 이벤트타입이 있는경우.
		elif self.event_info_data["locations"] == "None" and self.event_info_data["event_types"] != "None":						
			self.__event_reco_status_code = EventRecoStatusCode.RECO_NO_LOCA_HAS_EVENTTYPE




	

	def __reinForceForEventData(self):

		# 추천이 완벽할경우.값을 바로 사용할수있도록 한다.

		if self.__event_reco_status_code == EventRecoStatusCode.RECO_PERFECT:
			#DB에 값을넣고.
			locations = self.event_info_data["locations"]
			region = locations[0]["region"]
			surrounding_station =  self.__setSurroundingStation(region[:len(region)-1])				
			locations.append({
					"no" : 1,
					"region" : surrounding_station
				})

			#현재infojson을 그냥 사용할수있도록 패스합니다.
			self.event_reco_result = reinforce_result(EventRecoStatusCode.RECO_PERFECT.value,self.event_info_data)

		elif self.__event_reco_status_code == EventRecoStatusCode.RECO_CANT:
			#DB에 값을넣고.
			#현재infojson을 사용할수없게 값을 리턴해줍니다.
			self.event_reco_result = reinforce_result(EventRecoStatusCode.RECO_CANT.value,"None")

		#이벤트 타입이 있는데, 로케이션이 없다면, 
		#1. 유저 DB에서 가져와야 한다. 
		#2. 핫플레이스에서 가져와야한다. 		
		elif self.__event_reco_status_code == EventRecoStatusCode.RECO_NO_LOCA_HAS_EVENTTYPE:		

		#TODO 핫플레이스를 넣어준다.
			rows = utils.fetch_all_json(
					db_manager.query(
							"""
							SELECT region, count(*) as locationCnt FROM
							(
							SELECT ul.region,ul.location_hashkey,ul.priority 
							FROM EVENT e, USER_EVENT_ANALYSIS ue , USER_EVENT_LOCATION ul ,
							(
							# 여기까지 유저 accounthashkey가 같은 calendar 가져오기
							SELECT calendar_hashkey FROM CALENDAR
							INNER JOIN(
							#여기까지 이벤트 해시키로 유저 account_hashkey들 가져오는쿼리
							SELECT account_hashkey FROM USERACCOUNT
							WHERE user_hashkey IN (
							SELECT user_hashkey 
							FROM EVENT e, CALENDAR c, USERACCOUNT u
							WHERE e.event_hashkey = %s
							AND c.calendar_hashkey = e.calendar_hashkey
							AND u.account_hashkey = c.account_hashkey
							)	
							#############
							) AS u
							ON u.account_hashkey = CALENDAR.account_hashkey
							#############
							) cal
							WHERE e.calendar_hashkey = cal.calendar_hashkey
							AND ue.event_hashkey = e.event_hashkey
							AND ue.location_hashkey = ul.location_hashkey
							AND ul.priority = 1
							) AS locations
							GROUP by region

							""",
							(self.event_info_data["event_hashkey"],)
					)
			)
			new_locations = []
			#유저데이터가 있을경.
			if len(rows) != 0:
				region = rows[0]["region"]				
				new_locations.append({
						"no" : 0,
						"region" : rows[0]["region"]
					})
				
				surrounding_station =  self.__setSurroundingStation(region[:len(region)-1])				
				new_locations.append({
						"no" : 1,
						"region" : surrounding_station
					})
				



			#유저데이터가 없을때
			else:
				rows = utils.fetch_all_json(
					db_manager.query(
							"""
							SELECT * FROM
							(SELECT * FROM DEFAULT_HOT_PLACE ORDER BY rand() LIMIT 2 ) AS e
							ORDER BY id
							""",							
					)
				)
				for idx,row in enumerate(rows):	
					new_locations.append({
							"no" : idx,
							"region" : row["region"]
					})				
			
			self.event_info_data["locations"] = new_locations
		# 	print(self.event_info_data)
			self.event_reco_result = reinforce_result(EventRecoStatusCode.RECO_NO_LOCA_HAS_EVENTTYPE.value,self.event_info_data)

	def __setSurroundingStation(self,station_name):		
		rows = utils.fetch_all_json(
				db_manager.query(
						"""
					SELECT surrounding_station FROM SUBWAY_INFO
					WHERE station_name = %s
					limit 1
						""",
						(station_name,)
				)
		)					
		return rows[0]["surrounding_station"]	

				