import os
import flask
import pickle
import sys, fitz
from flask import Flask, request, url_for, render_template, send_from_directory
from itertools import *
import time
import random
from werkzeug.utils import secure_filename
import requests
from pdfreader import PDFReader
import sqlite3

import spacy

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'

model_path = 'model/model_2'
model = spacy.load(model_path)

app = Flask(__name__, static_url_path="/static")

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')

@app.route("/signup")
def signup():

    username = request.args.get('user','')
    name = request.args.get('name','')
    email = request.args.get('email','')
    number = request.args.get('mobile','')
    password = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
    con.commit()
    con.close()
    return render_template("signin.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('user','')
    password1 = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        return render_template("signin.html")    

    elif mail1 == 'admin' and password1 == 'admin':
        return render_template("index.html")

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("index.html")
    else:
        return render_template("signup.html")

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
   return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/main', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        f = request.files.getlist('files')
        result = []

        for file in f:
            if file:
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                doc = fitz.open(upload_dir)
                text = ""
                for page in doc:
                    text = text + str(page.getText())
                
                tx = "".join(text.split('\n'))
                doc = model(tx)
                # entities = {key: list(g) for key, g in groupby(sorted(doc.ents, key=lambda x: x.label_), lambda x: x.label_)}
                entities = {key: list(set(map(lambda x: str(x), g))) for key, g in groupby(sorted(doc.ents, key=lambda x: x.label_), lambda x: x.label_)}

                result.append(entities)

        return render_template('result.html', result=result)

    return render_template('index.html')

@app.route('/upload')
def upload():
   return render_template('upload.html')

@app.route('/uploader', methods = ["GET","POST"])
def upload_file():
   if request.method == 'POST':
      f = request.files['zipfile']
      f.save(secure_filename(f.filename))
      #job_desc=request.form.get("jobdesc")
      #num_rank=request.form.get("rank")
      #req_details=[job_desc,num_rank]
      jd_skills=request.form.get("skills")
      c_sep_skills=jd_skills.split(',')
      final_skills=[]
      for skill in c_sep_skills:
         skill=skill.strip()
         skill=skill.replace(" " ,"_")
         final_skills.append(skill)
      
      reader=PDFReader()
      allresumes=reader.extract_resumes(f.filename)
      resumes_scores = {}
      for index in range(len(allresumes[0])):
         resume_score = reader.analyze_resume(allresumes[0][index], allresumes[1][index], index + 1, final_skills)
         resumes_scores[allresumes[1][index]] = resume_score

      return render_template('printresult.html', scores=resumes_scores, title="View Scores",skills=final_skills)

if __name__ == '__main__':
    app.run(debug=True)
