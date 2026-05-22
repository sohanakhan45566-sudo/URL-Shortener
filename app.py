from flask import Flask, request, redirect, render_template_string, jsonify
import pymongo
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB connection
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', 27017))

client = pymongo.MongoClient(mongo_host, mongo_port)
db = client['url_shortener']
urls_collection = db['urls']

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>URL Shortener</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; text-align: center; }
        input, button { padding: 10px; margin: 5px; }
        input { width: 70%; }
        .result { margin-top: 20px; padding: 10px; background: #e8f5e9; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🔗 URL Shortener</h1>
    <form method="POST">
        <input type="text" name="url" placeholder="Enter long URL" required>
        <button type="submit">Shorten</button>
    </form>
    {% if short_url %}
    <div class="result">
        <strong>Short URL:</strong><br>
        <a href="{{ short_url }}">{{ short_url }}</a>
    </div>
    {% endif %}
</body>
</html>
'''

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url = request.form.get('url')
        if not long_url.startswith(('http://', 'https://')):
            long_url = 'https://' + long_url
        
        # Check if URL already exists
        existing = urls_collection.find_one({'long_url': long_url})
        if existing:
            short_code = existing['short_code']
        else:
            short_code = generate_short_code()
            urls_collection.insert_one({
                'long_url': long_url,
                'short_code': short_code,
                'clicks': 0
            })
        
        short_url = request.host_url + short_code
        return render_template_string(HTML_TEMPLATE, short_url=short_url)
    
    return render_template_string(HTML_TEMPLATE, short_url=None)

@app.route('/<short_code>')
def redirect_url(short_code):
    url_data = urls_collection.find_one({'short_code': short_code})
    if url_data:
        urls_collection.update_one(
            {'short_code': short_code},
            {'$inc': {'clicks': 1}}
        )
        return redirect(url_data['long_url'])
    return "URL not found", 404

@app.route('/stats/<short_code>')
def stats(short_code):
    url_data = urls_collection.find_one({'short_code': short_code})
    if url_data:
        return jsonify({
            'long_url': url_data['long_url'],
            'short_code': url_data['short_code'],
            'clicks': url_data.get('clicks', 0)
        })
    return jsonify({'error': 'Not found'}), 404

@app.route('/health')
def health():
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)