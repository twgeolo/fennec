from flask import Flask, jsonify, request, url_for
from websocket_server import WebsocketServer
from Queue import Queue
import requests
import json

app = Flask(__name__)

#Max Number of stations
maxNumStations = 100

class mediaObject:
	def __init__(self):
		self.id = ''
		self.uri = ''
		self.thubnail = ''
		self.length = ''
		self.addedBy = ''

class stationObject:
	def __init__(self):
		self.name = ''		
		self.queue = Queue()

stationList = [ stationObject() for i in range(maxNumStations)]

@app.route('/')
def index():
	return "Please use /api/"

@app.route('/api/create', methods=['POST'])
def addStation():
	#TODO: Parse JSON object, create new station and return stationid
	return 201


@app.route('/api/<int:stationid>/add', methods=['POST'])
def addMedia(stationid):
	#TODO: Parse JSON object and store in queue stationid
	media = mediaObject()
	media.id = '1'
	media.uri= 'https://www.youtube.com/watch?v=IuysY1BekOE',
	media.thumbnail = 'https://i.ytimg.com/vi/IuysY1BekOE/mqdefault.jpg',
	media.length = '0:05',
	media.addedBy = 'Tim'
	
	stationList[stationid].queue.put(media)
	print("added ID 1")
	return jsonify({'result': 'Media added'}),201

@app.route('/api/<int:stationid>/next', methods=['GET'])
def nextMedia(stationid):

#	print(stationList[stationid].queue.get())
	nextItem = stationList[stationid].queue.get()
	media = {
		'id' : nextItem.id,
		'uri': nextItem.uri,
		'thumbnail': 'https://i.ytimg.com/vi/IuysY1BekOE/mqdefault.jpg',
		'length': '0:05',
		'addedBy': 'Tim'
	}
	print(media)

	return jsonify(media),201

@app.route('/api/<int:stationid>', methods=['GET'])
def allMedia(stationid):
	queue = [{}]
	queue[0]['id'] = '1'
	queue[0]['uri'] = 'https://www.youtube.com/watch?v=IuysY1BekOE'
	queue[0]['thumbnail'] = 'https://i.ytimg.com/vi/IuysY1BekOE/mqdefault.jpg'
	queue[0]['length'] = '0:05'
	queue[0]['addedBy']= 'Tim'
	#TODO: Return full queue for station stationid
	return jsonify(queue[0]),201

@app.route('/api/<int:stationid>/remove', methods=['POST'])
def removeMedia(stationid):
	#TODO: Parse JSON object and remove it for the station's queue if exists
	return jsonify({'status':'success'}), 201

@app.route('/api/search/youtube', methods=['GET'])
def searchYouTube():
	q = request.args.get('q')
	if not q:
		return jsonify({'status':'failure', 'description':'missing argument \'q\''}), 201
	response = requests.get('https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&order=relevance&q=' + q + '&type=video&videoDefinition=any&key=AIzaSyASsdIg2A2eb-W9UlfOx4sIVRLZ2y1h63c')
	json_obj = response.json()
	items = json_obj['items']
	d = request.args.get('debug')
	if d and d != 'true' and d != 'false':
		return jsonify({'status':'failure', 'description':'argument \'d\' should be \'true\' or \'false\''}), 201
	if not d or d == 'false':
		for item in items:
			for key, value in item['snippet'].items():
				item[key] = value
			item['videoId'] = item['id']['videoId']
			if item['thumbnails']['high']:
				item['thumbnailUrl'] = item['thumbnails']['high']['url']
			elif item['thumbnails']['medium']:
				item['thumbnailUrl'] = item['thumbnails']['medium']['url']
			else:
				item['thumbnailUrl'] = item['thumbnails']['default']['url']
			item['videoUrl'] = 'https://www.youtube.com/watch?v=' + item['videoId']
			del item['etag'], item['kind'], item['id'], item['snippet'], item['channelId'], item['liveBroadcastContent'], item['thumbnails']
	return jsonify({'status':'success', 'items':items}), 201 

@app.route('/api/search/soundcloud', methods=['GET'])
def searchSoundCloud():
	q = request.args.get('q')
	if not q:
		return jsonify({'status':'failure', 'description':'missing argument \'q\''}), 201
	response = requests.get('http://api.soundcloud.com/tracks.json?client_id=87dd0b14dbc81970b9b4becdf176c498&q=' + q + '&limit=10')
	json_obj = response.json()
	d = request.args.get('debug')
	if d and d != 'true' and d != 'false':
		return jsonify({'status':'failure', 'description':'argument \'d\' should be \'true\' or \'false\''}), 201
	if not d or d == 'false':
		for item in json_obj:
			item['thumbnail'] = item['artwork_url']
			item['videoUrl'] = item['video_url']
			item['waveformUrl'] = item['waveform_url']
			item['trackUrl'] = item['permalink_url']
			item['playCount'] = item['playback_count']
			item['lastModified'] = item['last_modified']
			item['trackId'] = item['id']
			item['format'] = item['original_format']
			item['publishedAt'] = item['created_at']
			item['uploader'] = item['user']['username']
			del item['user'], item['user_favorite'], item['user_id'], item['user_playback_count'], item['video_url'], item['waveform_url'], item['state'], item['stream_url'], item['streamable'], item['tag_list'], item['track_type'], item['uri'], item['sharing'], item['reposts_count'], item['release_year'], item['release_month'], item['release_day'], item['release'], item['purchase_url'], item['purchase_title'], item['permalink'], item['permalink_url'], item['playback_count'], item['license'], item['likes_count'], item['last_modified'], item['label_name'], item['label_id'], item['kind'], item['key_signature'], item['isrc'], item['id'], item['original_format'], item['original_content_size'], item['genre'], item['favoritings_count'], item['embeddable_by'], item['downloadable'], item['download_url'], item['download_count'], item['created_at'], item['commentable'], item['comment_count'], item['bpm'], item['attachments_uri'], item['artwork_url']
	return jsonify({'status':'success', 'items':json_obj}), 201

if __name__ == '__main__':
	app.run(port=2000,debug=True)

#Beginning of Chat websocket implementation

chat_station_users = [] #chat_station_users[stationid] = list_of_users
station_index = 0

#Just join chat services
def new_client(client, server):
	print("%d connected" % client['id'])
	server.send_message_to_all("New Client")

#Just leave chat services
def client_left(client, server):
	print("%d disconnected" % client['id'])

#Redirect to handlers or send message
def message_received(client, server, message):
	json_obj = message.json();
	if json_obj['type'] == 'send':
		#Send normal message
		for c in chat_station_users[json_obj['stationid']]:
			server.send_message(c, json_obj['message'])
	elif json_obj['type'] == 'join':
		#Join station
		client_join_chat_station(client, json_obj['stationid'])
	elif json_obj['type'] == 'leave':
		#Leave station
		client_leave_chat_station(client, json_obj['stationid'])
	

#Put client into specific station
def client_join_chat_station(client, stationid):
	chat_station_users[stationid].append(client)
	return

#Remove client from specific station
def client_leave_chat_station(client, stationid):
	chat_station_users[stationid].remove(client)
	return

server = WebsocketServer(5000)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.run_forever()

#End of Chat websocket implementation
