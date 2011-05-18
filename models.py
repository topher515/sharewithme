from google.appengine.ext import db
#from google.appengine.api import memcache
from google.appengine.ext.blobstore import BlobReferenceProperty
from string import letters, digits

VALID_KEY_CHARS = digits + letters + '-_+'
COUNTER_NAME = 'upload-counter'

class UploadCounter(db.Model):
	""" Count the number of uploads so that the next upload 
	gets the next available ID """
	count = db.IntegerProperty(default=0)

	@staticmethod
	def increment():
		def txn():
			counter = UploadCounter.get_by_key_name(COUNTER_NAME)
			if counter is None:
				counter = UploadCounter(key_name=COUNTER_NAME)
			counter.count += 1
			counter.put()
		db.run_in_transaction(txn)
		
	@staticmethod
	def get_count():
		counter = UploadCounter.get_by_key_name(COUNTER_NAME)
		if counter is None:
			return 0
		else:
			return counter.count
		
	@staticmethod	
	def get_then_increment():
		def txn():
			counter = UploadCounter.get_by_key_name(COUNTER_NAME)
			if counter is None:
				counter = UploadCounter(key_name=COUNTER_NAME)
			c = counter.count
			counter.count += 1
			counter.put()
			return c
		return db.run_in_transaction(txn)
		
		
class UserData(db.Model):
	blob_info = BlobReferenceProperty()
	
	@staticmethod
	def create(blob_info):
		key_name = UserData.int_to_key_name(UploadCounter.get_then_increment())
		u = UserData(key_name=key_name,blob_info=blob_info)
		u.put()
	 	return u
	
	@staticmethod
	def int_to_key_name(i):
		key_name = []
		while i > 0:
			index = i % len(VALID_KEY_CHARS)
		 	i = i / len(VALID_KEY_CHARS)
			key_name.append(VALID_KEY_CHARS[index])
		return ''.join(key_name)