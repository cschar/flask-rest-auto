from flask import Flask, request, send_from_directory, Response
from flask.ext.restful import reqparse, abort, Api, Resource
from sys import argv
import werkzeug
import os
import json


UPLOAD_FOLDER = './images'
myapp = Flask(__name__)

api = Api(myapp)

#Fields sent in text, and not binary (photo field)
TXT_FIELDS = ["description","engine","make","year","owner"]

#in memory test db
class MemDatabase():
	def __init__(self):
		self.db = {}
	def init_data(self,data):
		self.db = data

	def get_all_items(self):
		return self.db

	def set_item(self,car_id, item_data):
		key = 'id'+str(car_id)
		self.db[key] = item_data
		return self.db[key]

	def partially_update_item(self,car_id, partial_item_data):
		key = 'id'+str(car_id)
		item = self.db[key]
		new_item_data = {}
		for field in partial_item_data.keys():
			new_item_data[field] = partial_item_data[field]

		for field in item.keys():
			if not field in partial_item_data.keys():
				new_item_data[field] = item[field]
		self.set_item(car_id,new_item_data)

	def get_item(self,car_id):
		return self.db["id"+str(car_id)]

	def contains(self,car_id):
		if self.db.has_key("id"+str(car_id)):
			return True
		else:
			return False

	def remove_item(self,car_id):
		if self.contains(car_id):
			del self.db["id"+str(car_id)]
	def get_size(self):
		return len(self.db)


db_data = {
	'id1': {
			"description":"roadster",
			"engine":"1300",
			"make":"honda",
			"year":"1988",
			"name":"john",
			"photo":"/static/images/default.jpg"
			},
	'id2': {	"description":"rhog",
			"engine":"1300",
			"make":"honda",
			"year":"1988",
			"name":"john",
			"photo":"/static/images/default.jpg"
			},

}

db = MemDatabase()
db.init_data(db_data)



parser = reqparse.RequestParser()
parser.add_argument('json_str', type=str)
parser.add_argument('photoupload', type=werkzeug.datastructures.FileStorage,
					location='files')



@myapp.route('/images/<filename>')
def uploaded_file(filename):
	return send_from_directory(myapp.config['UPLOAD_FOLDER'],filename)

@myapp.route('/')
def index():
	ret = "<html>"
	for i in os.environ:
		ret += str(i) + " : " + os.environ[i] 
		ret += "</br>\n"
	ret += "</html>"
	return ret




class Car(Resource):
	def get(self, car_id):
		
		if not db.contains(car_id):
			msg = "Invalid car id requested"
			return msg, 404
		return db.get_item(car_id)

	def delete(self, car_id):
		if not db.contains(car_id):
			msg = "Can't delete, no value for id"
			return msg, 404

		db.remove_item(car_id)
		return {}, 200

	def put(self, car_id):
		args = parser.parse_args()  # (json_str : {... }, 'photoupload' : <file>)
		if args['json_str'] == None:
			msg = "communicate with json inside field : 'json_str'"
			return msg,404

		js_dict = json.loads(args['json_str'])
		if not(args['photoupload'] and has_all_valid_fields(js_dict,TXT_FIELDS)):
			msg = "Bad fields in json"
			return msg,404

		photo_savepath = save_photoupload(request,car_id)
		js_dict["photo"] = photo_savepath[1:] #remove the .

		new_item = db.set_item(car_id,js_dict)
		return new_item, 200

	def patch(self, car_id):
		args = parser.parse_args()  # (json_str : {... }, 'photoupload' : <file>)
		if args['json_str'] == None:
			msg = "communicate with json inside field : 'json_str'"
			return msg,404

		js_dict = json.loads(args['json_str'])
		if not has_valid_fields(js_dict,TXT_FIELDS):
			msg = "Bad fields in json"
			return msg,404

		if args['photoupload']:
			photo_savepath = save_photoupload(request,car_id)
			js_dict["photo"] = photo_savepath[1:] #remove the .

		
		db.partially_update_item(car_id,js_dict)
		patched_item = db.get_item(car_id)
		return patched_item, 200

class CarList(Resource):
	def get(self):
		return db.get_all_items()

	def post(self):
		args = parser.parse_args()  # (json_str : {... }, 'photoupload' : <file>)
		if args['json_str'] == None:
			msg = "communicate with json inside field : 'json_str'"
			return msg,404

		js_dict = json.loads(args['json_str'])
		car_id = db.get_size() + 1
		if not(args['photoupload'] and has_all_valid_fields(js_dict,TXT_FIELDS)):
			msg = "Bad fields in json"
			return msg,404

		photo_savepath = save_photoupload(request,car_id)

	
		js_dict["photo"] = photo_savepath[1:] #remove the .
		new_item = db.set_item(car_id,js_dict)
		return new_item, 201,{'Location':'/cars/'+str(car_id)}



def save_photoupload(request,car_id):
	photo_savepath="not set"
	if request.files.has_key('photoupload'):
		photo_file = request.files['photoupload']
		unique_filename = get_clean_filename(photo_file.filename,car_id)
		photo_savepath = "./static/images/"+ unique_filename
		save_file(photo_file,photo_savepath)
	return photo_savepath

def get_clean_filename(filename,car_id):
	name = filename.replace("../","").replace("./","")
	return str(car_id) + "_" + name

def save_file(fil,path):
	data = fil.read()
	try:
		path = path.encode('ascii','ignore')
		f = open(path,"wb")
		f.write(data)
		f.close()
		return path
	except IOError as e:
		print e
		return ""

def has_valid_fields(dictionary,list_of_fields):
	for field in dictionary.keys():
		if not field in list_of_fields:
			return False
	return True

def has_all_valid_fields(dictionary,list_of_fields):
	for field in list_of_fields:
		if not dictionary.has_key(field):
			return False
	return True

#Add resources after defining above
api.add_resource(CarList, '/cars')
api.add_resource(Car, '/cars/<string:car_id>')

if __name__ == '__main__':
	app_port = argv[1] if len(argv) > 1 else 8080
	myapp.run(debug=True,port=int(app_port))