from bottle import route, run, template, static_file, url, HTTPResponse, redirect
from bottle import get, post, request, response, error
from bottle import hook, route, response
from mirai_translate import Client
import sqlite3
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@route('/', method="GET")
def html_index():
    return template('static/start')

@route("/go_home",method=["POST"])
def go_home():
    return template('static/home')

@route("/go_past",method="GET")
def go_home():
    text_list = get_text()
    return template('static/past_work', text_list = text_list)


@route("/add_Text",method=["POST"])
def add_Text():
    cli = Client()
    jpText = request.forms.JapaneseText
    engText = request.forms.EnglishText
    engTrans = cli.translate(jpText, 'ja', 'en')
    similarity = calculate_similarity(engText, engTrans)
    similarity = round(similarity,1)
    #result_textを定める項
    if similarity == 100.0:
        result_text = 'Excellent!'
    elif similarity >= 70.0:
        result_text = 'Good! Keep trying!'
    else:
        result_text = 'Try again! You can do it!'
    ##########
    if similarity == 100.0:
        advice = 'Your traslation was perfect! Keep it up!'
    else:
        advice = create_advice(engText, engTrans)
    #####
    save_texts(jpText, engText, engTrans, str(similarity))
    return template('static/result', similarity = str(similarity), jpText = jpText, engText = engText, engTrans = engTrans, result_text = result_text, advice = advice)


@route("/del_text",method=["POST"])
def del_text():
    con = sqlite3.connect("translate_database.db")
    c = con.cursor()

    name = request.POST.get("complete")
    if name:
        delete="delete from sentences where engText = '" + name + "'"
        c.execute(delete)
        con.commit()
    return redirect("/go_past")

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root = './static')


def get_text():
    con = sqlite3.connect('translate_database.db')
    c = con.cursor()
    select = "SELECT * FROM sentences"
    c.execute(select)
    result = c.fetchall()
    return result

def save_texts(jpText, engText, engTrans, similarity):
    con = sqlite3.connect('translate_database.db')
    c = con.cursor()
    insert = "INSERT INTO sentences(jpText, engText, engTrans, similarity) VALUES (?, ?, ?, ?)"
    c.execute(insert, (jpText, engText, engTrans, similarity))
    con.commit()

def preprocess_text(text):
    nlp = spacy.load('en_core_web_sm')
    # テキストの前処理を行う関数
    doc = nlp(text.lower())
    #tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    tokens = [token.lemma_ for token in doc if token.is_alpha]
    return ' '.join(tokens)

def calculate_similarity(text1, text2):
    # 2つの文章の類似度を計算する関数
    preprocessed_text1 = preprocess_text(text1)
    preprocessed_text2 = preprocess_text(text2)
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([preprocessed_text1, preprocessed_text2])
    similarity = cosine_similarity(vectors)[0][1]
    return similarity * 100

def process_for_advice(text):
    nlp = spacy.load('en_core_web_sm')
    # テキストの前処理を行う関数
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return set(tokens)

def create_advice(text1, text2):
    process_for_advice1 = process_for_advice(text1)
    process_for_advice2 = process_for_advice(text2)
    if process_for_advice1 == process_for_advice2:
        advice_word = 'You are probably making a grammatical mistake!'
    else:
        advice_word = 'You are probably using the wrong word!'
    return advice_word


run(host='localhost', port=8088, debug=True)