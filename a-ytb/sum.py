from flask import Flask, render_template, request, jsonify, make_response
from flask_socketio import SocketIO, join_room, emit
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob
from bs4 import BeautifulSoup
import csv
import io
import pandas as pd
import nltk
import os
import re



nltk.download("stopwords")
from nltk.corpus import stopwords

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize Youtube API
API_KEY = 'AIzaSyC_2R_l595WcYINW7vHSwGJnp3PBb087CU'
youtube = build('youtube', 'v3', developerKey=API_KEY)


# Configure file uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cache for loaded data
data_cache = {}

def load_data(file_path):
    if file_path in data_cache:
        return data_cache[file_path]
    else:
        data = pd.read_csv(file_path)
        data_cache[file_path] = data
        return data

# Custom secure filename function
def custom_secure_filename(filename):
    filename = filename.replace(' ', '_')  # Replace spaces with underscores
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)  # Remove any non-alphanumeric characters except ._-
    return filename

@app.route("/topic")
def topic():
    return render_template("topic.html")

@app.route("/upload_and_analyze", methods=["POST"])
def upload_and_analyze():
    comment = request.form['comment']
    file = request.files['file']
    filename = custom_secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    data = load_data(file_path)
    pos_comments = data["Positive Comments"].dropna().unique().tolist()
    neg_comments = data["Negative Comments"].dropna().unique().tolist()
    analyzer = SentimentIntensityAnalyzer()
    vader_sentiment = analyzer.polarity_scores(comment)["compound"]
    
    #Sentiment analysis using TextBlob
    blob = TextBlob(comment)
    textblob_sentiment = blob.sentiment.polarity
    
    # Determine sentiment based on both methods
    if vader_sentiment >= 0 and textblob_sentiment >=0:
        result = "Positive"
    else:
        result = "Negative"
    return jsonify({"sentiment": result})



def fetch_comments_and_analyze(video_id):
    # Fetch video details
    video_request = youtube.videos().list(part='snippet', id=video_id)
    video_response = video_request.execute()
    video_title = video_response['items'][0]['snippet']['title']
    video_description = video_response['items'][0]['snippet']['description']

    # Fetch comments
    comments = []
    nextPageToken = None
    while len(comments) < 2000:
        request = youtube.commentThreads().list(
            part='snippet', videoId=video_id, maxResults=100, pageToken=nextPageToken)
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break

    comments = [BeautifulSoup(comment, "html.parser").get_text() for comment in comments]

    analyzer = SentimentIntensityAnalyzer()
    sentiment_data = []
    for comment in comments:
        sentiment_score = analyzer.polarity_scores(comment)
        sentiment_data.append({
            'text': comment,
            'compound': sentiment_score['compound']
        })

    sentiment_data.sort(key=lambda x: x['compound'], reverse=True)
    positive_count = len([comment for comment in sentiment_data if comment['compound'] > 0])
    negative_count = len([comment for comment in sentiment_data if comment['compound'] < 0])
    neutral_count = len(sentiment_data) - positive_count - negative_count
    positive_comments = sentiment_data[:10]
    negative_comments = sentiment_data[-10:]
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(['Comment', 'Compound Score'])
    for comment in sentiment_data:
        csv_writer.writerow([comment['text'], comment['compound']])

    return {
        'videoTitle': video_title,
        'videoDescription': video_description,
        'positiveComments': positive_comments,
        'negativeComments': negative_comments,
        'positiveCount': positive_count,
        'negativeCount': negative_count,
        'neutralCount': neutral_count,
        'csvData': csv_data.getvalue(),
        'allPositiveComments': [comment['text'] for comment in sentiment_data if comment['compound'] > 0],
        'allNegativeComments': [comment['text'] for comment in sentiment_data if comment['compound'] < 0]
    }
def get_related_videos(video_title, video_description):
    query = video_title if video_title else video_description
    search_request = youtube.search().list(part='snippet', q=query, type='video', maxResults=10)
    search_response = search_request.execute()
    related_videos = []
    for item in search_response['items']:
        video_info = {
            'videoId': item['id']['videoId'],
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'thumbnail': item['snippet']['thumbnails']['high']['url']
        }
        related_videos.append(video_info)
    return related_videos

users = {'customer': '', 'operator': ''}

@app.route("/")
def index():
    return render_template("index.html")

# Other routes and SocketIO events remain unchanged...

@app.route("/analyze", methods=["GET"])
def analyze():
    video_url = request.args.get('videoUrl')
    video_id = video_url.split('v=')[-1]
    sentiment_data = fetch_comments_and_analyze(video_id)

    related_videos = get_related_videos(sentiment_data['videoTitle'], sentiment_data['videoDescription'])
    sentiment_data['relatedVideos'] = related_videos
    socketio.emit('related_videos', {'videos': sentiment_data['relatedVideos']}, room='customer_room')

    # Notify customer to show the export button
    socketio.emit('analysis_complete', {'videoUrl': video_url}, room='customer_room')

    return jsonify(sentiment_data)
@socketio.on('send_database')
def on_send_database(data):
    emit('show_export_button', {'videoUrl': data['videoUrl']}, room='customer_room')
@socketio.on('send_related_videos')
def send_related_videos():
    socketio.emit('show_related_videos_button', room='customer_room')
@app.route("/export", methods=["GET"])
def export():
    video_url = request.args.get('videoUrl')
    video_id = video_url.split('v=')[-1]
    sentiment_data = fetch_comments_and_analyze(video_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(['Title', 'Total Comments', 'Positive Count', 'Negative Count', 'Positive Comments', 'Negative Comments'])

    # Determine the maximum number of positive and negative comments
    max_len = max(len(sentiment_data['allPositiveComments']), len(sentiment_data['allNegativeComments']))

    # Write rows for each comment
    for i in range(max_len):
        # If positive comments are available, get the comment; otherwise, leave it empty
        positive_comment = sentiment_data['allPositiveComments'][i] if i < len(sentiment_data['allPositiveComments']) else ''
        # If negative comments are available, get the comment; otherwise, leave it empty
        negative_comment = sentiment_data['allNegativeComments'][i] if i < len(sentiment_data['allNegativeComments']) else ''
        
        # Write row with title, total comments count, positive count, negative count, positive comment, and negative comment
        # Only write title, total comments count, positive count, negative count in the first row
        if i == 0:
            writer.writerow([sentiment_data['videoTitle'], len(sentiment_data['allPositiveComments']) + len(sentiment_data['allNegativeComments']), sentiment_data['positiveCount'], sentiment_data['negativeCount'], positive_comment, negative_comment])
        else:
            # For subsequent rows, leave first four columns empty
            writer.writerow(['', '', '', '', positive_comment, negative_comment])

    output.seek(0)

    # Set up response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=sentiment_comments.csv'
    response.headers['Content-type'] = 'text/csv'
    return response



@socketio.on('connect')
def connect():
    print('Client connected')

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

@app.route('/customer')
def customer():
    return render_template('customers.html', user_type='customer')

@app.route('/operator')
def operator():
    return render_template('index.html', user_type='operator')

@app.route('/customer2')
def customer2():
    return render_template('customers.html', user_type='customer2')

@socketio.on('join_room')
def handle_join_room(data):
    username = data['username']
    room = data['room']
    users[username] = room
    join_room(room)  # Join the specific room corresponding to the customer
    emit('user_joined', {'username': username, 'room': room}, room=room)

@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    message = data['message']
    sender_room = users.get(username)  # Room of the sender
    receiver_room = 'operator_room'  # Room of the operator

    if sender_room:
        emit('receive_message', {'username': username, 'message': message}, room=receiver_room)  # Send message to the operator room
        emit('receive_message', {'username': username, 'message': message}, room=sender_room)  # Send message back to the sender
    else:
        print(f"User {username} not found in any room")

if __name__ == "__main__":
    socketio.run(app, debug=True)
