from urllib.parse import unquote, urlparse
from flask import Flask, render_template, request, session, redirect, url_for
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'wikirace_secret_key'

HEADERS = {'User-Agent': 'WikiRaceGame/1.0 (learning_project)'}

def clean_title(input_text):
    text = unquote(input_text.strip())
    if 'wikipedia.org/wiki/' in text:
        parsed = urlparse(text)
        return parsed.path.split('/wiki/')[-1]
    return text.replace(' ', '_')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start = clean_title(request.form.get('start_url'))
        target = clean_title(request.form.get('target_url'))
        session['start'] = start
        session['target'] = target
        session['clicks'] = 0
        session['path'] = [start]
        return redirect(url_for('play', title=start))
    return render_template('index.html')

@app.route('/play/<title>')
def play(title):
    if 'target' not in session:
        return redirect(url_for('index'))
    
    target = session['target']
    
    if title.lower() == target.lower():
        return render_template('win.html', clicks=session.get('clicks', 0), path=session.get('path', []), target=target)

    resp = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/html/{title}", headers=HEADERS)
    if resp.status_code != 200:
        return "Article not found", 404

    soup = BeautifulSoup(resp.text, 'html.parser')

    for tag in soup.find_all(['header', 'footer', 'nav', 'sidebar']):
        tag.decompose()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('./') or href.startswith('/wiki/'):
            next_title = href.replace('./', '').replace('/wiki/', '')
            a['href'] = url_for('track', title=next_title)
        else:
            a['href'] = '#'

    return render_template('game.html', content=str(soup), title=title, target=target, clicks=session.get('clicks', 0))

@app.route('/track/<title>')
def track(title):
    session['clicks'] = session.get('clicks', 0) + 1
    path = session.get('path', [])
    path.append(title)
    session['path'] = path
    return redirect(url_for('play', title=title))

if __name__ == '__main__':
    app.run(debug=True)