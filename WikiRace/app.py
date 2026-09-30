import time
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
        start = clean_title(request.form.get('start_url', ''))
        target = clean_title(request.form.get('target_url', ''))
        session['start'] = start
        session['target'] = target
        session['clicks'] = 0
        session['path'] = [start]
        session['start_time'] = time.time()
        return redirect(url_for('play', title=start))
    return render_template('index.html')

@app.route('/play/<path:title>')
def play(title):
    if 'target' not in session:
        return redirect(url_for('index'))
    
    target = session['target']
    
    if title.lower().replace('_', ' ') == target.lower().replace('_', ' '):
        total_time = int(time.time() - session.get('start_time', time.time()))
        clicks = session.get('clicks', 0)
        
        highscore = session.get('highscore')
        if highscore is None or clicks < highscore:
            session['highscore'] = clicks
            highscore = clicks

        return render_template('win.html', clicks=clicks, path=session.get('path', []), target=target, time=total_time, highscore=highscore)

    elapsed_time = int(time.time() - session.get('start_time', time.time()))

    resp = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/html/{title}", headers=HEADERS)
    if resp.status_code != 200:
        return f"<h1>Article '{title}' not found</h1>", 404

    soup = BeautifulSoup(resp.text, 'html.parser')

    for tag in soup.find_all(['header', 'footer', 'nav', 'sidebar', 'base']):
        tag.decompose()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('./') or href.startswith('/wiki/'):
            clean_link = href.split('#')[0].replace('./', '').replace('/wiki/', '')
            if clean_link:
                a['href'] = url_for('track', title=clean_link, _external=True)
            else:
                a['href'] = '#'
        else:
            a['href'] = '#'

    return render_template(
        'game.html',
        content=str(soup),
        title=title.replace('_', ' '),
        target=target.replace('_', ' '),
        clicks=session.get('clicks', 0),
        time=elapsed_time,
        highscore=session.get('highscore', 'N/A')
    )

@app.route('/track/<path:title>')
def track(title):
    session['clicks'] = session.get('clicks', 0) + 1
    path = session.get('path', [])
    path.append(title)
    session['path'] = path
    return redirect(url_for('play', title=title))

@app.route('/restart')
def restart():
    hs = session.get('highscore')
    session.clear()
    if hs is not None:
        session['highscore'] = hs
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)