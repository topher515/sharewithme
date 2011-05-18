import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.images import get_serving_url
from django.utils import simplejson as json
from models import UserData

IMAGE_MIMETYPES = ['image/jpeg','image/png','image/tiff','image/gif',]
SEND_AS_RAW_MIMETYPES = IMAGE_MIMETYPES

class UploadPageHandler(webapp.RequestHandler):
	""" Handle rendering the upload page. """
	def get(self):
		upload_url = blobstore.create_upload_url('/upload')
		self.response.out.write(template.render('templates/upload.html', {'upload_url':upload_url}))
		
class UploadUrlHandler(webapp.RequestHandler):
	""" Handle requests for a new upload url for the blobstore """
	def get(self):
		self.response.out.write(blobstore.create_upload_url('/upload?format=json'))
		
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		format = self.request.get('format','html')		
		try:
			user_upload = UserData.create(self.get_uploads()[0])
		except IndexError:
			self.error(404)
		self.redirect('/i/%s?format=%s' % (user_upload.key().name(),format))

class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self,site_key):
		
		# Get the file by the provided key name
		user_data = UserData.get_by_key_name(site_key)
		if not user_data:
			return self.error(404)
		
		if user_data.blob_info.content_type in SEND_AS_RAW_MIMETYPES:
			# If this is a picture or otherwise something the browser can just use, send it
			self.send_blob(user_data.blob_info)
		else:
			# Otherwise prompt the browser to Save As
			self.send_blob(user_data.blob_info,save_as=True)
		
class PreviewHandler(webapp.RequestHandler):
	def get(self,site_key):
		
		# Get the file by the provided key name
		user_data = UserData.get_by_key_name(site_key)
		if not user_data:
			return self.error(404)
		blob_info = user_data.blob_info
		
		# Figure out hostname so we can give 'full links'
		host_name = '/'.join([k for k in self.request.url.split('/')[:3]])
		
		# Build the response
		resp = {
			'name':blob_info.filename,
			'creation':blob_info.creation.strftime("%Y-%m-%d %H:%M:%S"),
			'download_url':'%s/%s' % (host_name,site_key),
			'url':'%s/%s' % (host_name,site_key),
			'type':blob_info.content_type,
			'size':blob_info.size,
			'size_in_kb':(blob_info.size)/1024,
			'info_url':'%s/i/%s' % (host_name,site_key),
			'thumbnail_url': get_serving_url(blob_info) if blob_info.content_type in IMAGE_MIMETYPES else ''
		}
		
		if self.request.get('format') == 'json':
			# If the requested format is json render to json
			return self.response.out.write(json.dumps(resp))
		else:
			# Otherwise render to html
			self.response.out.write(template.render('templates/viewer.html', resp))
		
handlers =	[
	(r'/upload$', UploadHandler),
	(r'/upload-url$', UploadUrlHandler),
	(r'/([\d\w]+)$', DownloadHandler),
	(r'/i/([\d\w]+)$', PreviewHandler),
	(r'/$',UploadPageHandler),
]

application = webapp.WSGIApplication(handlers, debug=True)

if __name__ == '__main__':
	run_wsgi_app(application)