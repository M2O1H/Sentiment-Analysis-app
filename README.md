# Sentiment-Analysis-app
A Sentiment Analysis app using the lexicon approach.
# YouTube Comment Sentiment Analysis

This repository contains a Flask web application that performs sentiment analysis on YouTube video comments. The application allows users to upload a CSV file with comments, analyze the sentiment of a specific comment, and fetch and analyze comments from a YouTube video. The sentiment analysis is performed using the VADER and TextBlob libraries.

## Features

- Upload and analyze a CSV file of comments.
- Perform sentiment analysis on a single comment.
- Fetch and analyze comments from a YouTube video.
- Export sentiment analysis results to a CSV file.
- Real-time updates and communication using Socket.IO.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed Python 3.6 or later.
- You have a Google API key with access to the YouTube Data API v3.
- You have installed the necessary Python libraries:
  - Flask
  - Flask-SocketIO
  - google-api-python-client
  - vaderSentiment
  - scikit-learn
  - textblob
  - beautifulsoup4
  - pandas
  - nltk

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2. Install the required libraries:

    ```bash
    pip install -r requirements.txt
    ```

3. Set your Google API key:

    Replace the `API_KEY` variable in `app.py` with your own Google API key.

    ```python
    API_KEY = 'YOUR_API_KEY'
    ```

4. Run the application:

    ```bash
    python app.py
    ```

## Usage

1. Open your web browser and go to `http://127.0.0.1:5000/`.

2. To upload and analyze a CSV file:
   - Go to the `Upload and Analyze` page.
   - Upload your CSV file and enter a comment for analysis.
   - Click the `Analyze` button to see the sentiment analysis results.

3. To analyze comments from a YouTube video:
   - Go to the `Analyze` page.
   - Enter the URL of the YouTube video.
   - Click the `Analyze` button to fetch and analyze the comments.
   - You can export the results to a CSV file by clicking the `Export` button.

4. To view related videos:
   - After analyzing a video, the related videos will be displayed on the page.

## File Structure

- `app.py`: The main Flask application file.
- `templates/`: Directory containing HTML templates.
  - `index.html`: The homepage template.
  - `topic.html`: The topic page template.
  - `customers.html`: The customer page template.
- `uploads/`: Directory where uploaded files are stored.
- `requirements.txt`: File listing the required Python libraries.

## Routes

- `/`: Home page.
- `/topic`: Topic analysis page.
- `/upload_and_analyze`: Endpoint for uploading and analyzing a CSV file.
- `/analyze`: Endpoint for analyzing comments from a YouTube video.
- `/export`: Endpoint for exporting analysis results to a CSV file.
- `/customer`: Customer page.
- `/operator`: Operator page.
- `/customer2`: Another customer page.

## WebSocket Events

- `connect`: Event triggered when a client connects.
- `disconnect`: Event triggered when a client disconnects.
- `join_room`: Event for joining a specific chat room.
- `send_message`: Event for sending messages in a chat room.
- `send_database`: Event for sending the database to the client.
- `send_related_videos`: Event for sending related videos to the client.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to contribute to this project by submitting issues or pull requests. For any questions, please contact [artmo9532@gmail.com].
