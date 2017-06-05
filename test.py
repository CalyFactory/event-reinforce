from common import db_manager
from common.util import utils

from reinforce import Reinforce
import unittest

import json 

with open('./testData.json') as test_data:
	test_data = json.load(test_data)




class TestReinForce(unittest.TestCase):

	def test_reinforceFunction(self):
		
		hasAll = test_data["hasAll"]
		reinforce = Reinforce(hasAll)
		print("1.hasAll result => "+str(reinforce.event_reco_result))		

		# noLocationNoEventType = test_data["noLocationNoEventType"]
		# reinforce = Reinforce(noLocationNoEventType)			
		# print("2. noLocationNoEventType result => "+str(reinforce.event_reco_result))

		# noLocationHasEventType = test_data["noLocationHasEventType00"]
		# reinforce = Reinforce(noLocationHasEventType)			
		# print("2. noLocationHasEventType result => "+str(reinforce.event_reco_result))

		# self.assertEqual(instance.event_InfoJson, 'expected_json')


if __name__ == '__main__':
	unittest.main()



# 1 위와 같은 방식이 맞는지..  펑션마다 확인해야하는지
# 2 input json파일 어떻게 넣는지.. 내가 하려는 방식이 맞는지
# 3 예상값이 random하게 나오는데 type만 확인하는방법이나. 

# instance.check_location_validation()