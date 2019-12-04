import gensim
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
import os
import io 
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from flask import Flask,request,make_response,session
from flask import jsonify 
from spacy.matcher import Matcher
import spacy
import Parser as parser
import pymongo as pym
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_cors import CORS,cross_origin
from flask_jwt_extended import JWTManager 
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt 
from werkzeug.utils import secure_filename
from pdfminer.layout import LAParams
from io import StringIO
from werkzeug import secure_filename
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity  


import json
from bson import json_util
#from flask_pymongo import PyMongo 

app = Flask(__name__)
#app.config['MONGO_DBNAME'] = 'db'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/'
connection = pym.MongoClient()
app.config['JWT_SECRET_KEY'] = 'secret'

#mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

CORS(app)
db = connection.test

Job_Description=db["Job_Desc"]
Job_Provider=db["Job_Provider"]
Job_Seeker=db["Job_Seeker"]
resume=db["CV_Attributes"]


def js_list(encoder, data):
    pairs = []
    for v in data:
        pairs.append(js_val(encoder, v))
    return "[" + ", ".join(pairs) + "]"

def js_dict(encoder, data):
    pairs = []
    for k, v in data.iteritems():
        pairs.append(k + ": " + js_val(encoder, v))
    return "{" + ", ".join(pairs) + "}"

def js_val(encoder, data):
    if isinstance(data, dict):
        val = js_dict(encoder, data)
    elif isinstance(data, list):
        val = js_list(encoder, data)
    else:
        val = encoder.encode(data)
    return val

 
def extract_text_from_pdf(pdf_path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
 
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, 
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
 
        text = fake_file_handle.getvalue()
 
    # close open handles
    converter.close()
    fake_file_handle.close()
 
    if text:
        return text
 
def create_tokenizer_score(new_series, train_series, tokenizer):
    """
    return the tf idf score of each possible pairs of documents
    Args:
        new_series (pd.Series): new data (To compare against train data)
        train_series (pd.Series): train data (To fit the tf-idf transformer)
    Returns:
        pd.DataFrame
    """

    train_tfidf = tokenizer.fit_transform(train_series)
    new_tfidf = tokenizer.transform(new_series)
    X = pd.DataFrame(cosine_similarity(new_tfidf, train_tfidf), columns=train_series.index)
    X['ix_new'] = new_series.index
    score = pd.melt(
        X,
        id_vars='ix_new',
        var_name='ix_train',
        value_name='score'
    )
    return score

def tfidf(jd,empno):
    
    cv_users = resume
    for document in cv_users.find():
        print (document)
    all_users = cv_users.find({})
    
    cvs = []
    emails = []
    for doc in all_users:
        cvs.append(doc['cv'])
        emails.append(doc['uid']) 
#        
    raw_documents = cvs
    print(cvs)
    cor = []
    for i in range(0, len(cvs)):
        review = re.sub('\uf0b7', '', raw_documents[i])
        review = review.lower()
        cor.append(review)
    train_set = pd.Series(cor)
    test_set = pd.Series(jd)
    tokenizer = TfidfVectorizer() # initiate here your own tokenizer (TfidfVectorizer, CountVectorizer, with stopwords...)
    score = create_tokenizer_score(train_series=train_set, new_series=test_set, tokenizer=tokenizer)
    print(score)
    print(len(cor))

    df = score#pd.DataFrame(list(zip(emails, x)), 
#               columns =['email', 'score']) 
    df['email'] = emails
    top_cand = df.nlargest(empno, 'score', keep='all')
    if top_cand['score'].max() > 0:
        applicant = Job_Seeker
        applicant_selected_name = []
        for index, row in top_cand.iterrows():
            app_id = applicant.find_one({"email" : row['email']})
            fn = app_id['firstname']
            ln = app_id['lastname']
            applicant_selected_name.append(fn+ " " + ln)
                
        top_cand['name'] = applicant_selected_name
        top_cand.drop(['ix_new','ix_train'],axis=1,inplace=True)
        print(top_cand)
        
        return top_cand.to_json(orient='records')
    else:
        df_empty = pd.DataFrame({'score' : []})
        df_empty['name'] = []
        df_empty['email'] = []
        return df_empty.to_json(orient='records')

@app.route('/')
def index():
    return "Hello"

@app.route('/recommend',methods=['POST','GET'])
@cross_origin(supports_credentials=True)
def recommend():
    email=request.headers['Authorization']
    d = json.loads(email)
    jid = d['taskid']
    print(jid)
    x = Job_Description.find_one({'_id': ObjectId(jid)})
    
    jd = str(x['job_description'])
    emp_no = x['cand']
    
    recommended = tfidf(jd,emp_no)
    #print(jd)
    #print(emp_no)
    return recommended

@app.route('/register', methods=["POST"])
@cross_origin(supports_credentials=True)
def register():
    users = Job_Seeker
    user2 = Job_Provider
    req=request.get_json(force=True)
    usertype = req['type']
    fname = req['firstname']
    lname = req['lastname']
    gender = req['gender']
    email = req['email']
    age = req['age']
    phone = req['phone']
    password = req['password']
    password = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')

    if usertype == 'jobApplicant':
        user_id = users.insert_one(
            {   "firstname" : fname,
                "lastname" : lname,
                "gender" : gender,
                "email" : email,
                "age" : age,
                "phone" : phone,
                "password" : password,
                "type" : usertype,
                "cv" : ""
            })
        print("Job applicant")
        #new_user = users.find_one({'_id': user_id})
        
    elif usertype == 'Recruiter':
       user_id = user2.insert_one(
            {   "firstname" : fname,
                "lastname" : lname,
                "gender" : gender,
                "email" : email,
                "age" : age,
                "phone" : phone,
                "type" : usertype,
                "password" : password
            })
       print("In job seeker")
       #new_user = user2.find_one({'_id': user_id})

    result = {'email': email + ' registered'}

    return jsonify({'result' : result})

@app.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def log():
    users = Job_Seeker
    user2 = Job_Provider
    req=request.get_json(force=True)
    email = req['username']
    password = req['password']
    result = ""

    response = users.find_one({'email': email})
    response2 = user2.find_one({'email': email})

    if response:
        if bcrypt.check_password_hash(response['password'], password):
            access_token = create_access_token(identity = {
                'firstname': response['firstname'],
                'lastname': response['lastname'],
                'email': response['email'],
                'gender':response['gender'],
                'age': response['age'],
                'phone': response['phone'],
                'usertype': response['type']
            })
            result = jsonify({'token':access_token})
        else:
            result = jsonify({"error":"Invalid username and password"})
    elif response2:
        if bcrypt.check_password_hash(response2['password'], password):
            access_token = create_access_token(identity = {
                'firstname': response2['firstname'],
                'lastname': response2['lastname'],
                'email': response2['email'],
                'gender':response2['gender'],
                'age': response2['age'],
                'phone': response2['phone'],
                'usertype': response2['type']
            })
            result = jsonify({'token':access_token})
        else:
            result = jsonify({"error":"Invalid username and password"})
    else:
        result = jsonify({"result":"No results found"})
    return result 


@app.route('/jobpost',methods=['POST'])
@cross_origin(supports_credentials=True)
def jobpost():
    users = Job_Description
    req=request.get_json(force=True)
    req2=request.headers['Authorization']
    
    jobtitle = req['jobTitle']
    JD = req['JD']
    cand = req['empNo']
    #print(request.headers)
    user_id = users.insert_one(
            {   "job_title" : jobtitle,
                "job_description" : JD,
                "cand" : cand,
                "jp_email" : req2
            })
    print("Inserted")
    x=str(user_id.inserted_id)
    #result = {'job title': jobtitle + ' registered'}
    if user_id:
        result = {   "job_title" : jobtitle,
                      "empNo" : cand,
                      "job_id" : x
                }
    return jsonify({'result' : result})
    

@app.route('/allJds',methods=['POST','GET'])
@cross_origin(supports_credentials=True)
def allJds():
    #req=request.get_json(force=True)
    users=Job_Description
    req2=request.headers['Authorization']
    print(req2)
    x = users.find({"jp_email" : req2}) 
    li = []
    for doc in x:
        print(doc)
        doc['_id'] = str(doc['_id'])
        li.append(doc)
        
    return jsonify(li)



@app.route('/delJd/<obj_id>',methods=["DELETE"])
@cross_origin(supports_credentials=True)
def delJd(obj_id):
    #req=request.get_json(force=True)
    x = Job_Description.delete_one({'_id': ObjectId(obj_id)})
    
    if x:
        return "Deleted"
    else:
        return "Error in deletion"

@app.route('/submitCV',methods=['POST'])
@cross_origin(supports_credentials=True)
def submitCV():
    #cv = request.files['file']
    uid=request.headers['Authorization']
    users = resume
    file = request.files['file']
    filename = secure_filename(file.filename) 
    file.save(os.path.join("D:",filename))
    text = extract_text_from_pdf(os.path.join("D:",filename))
    print(text)
    #text        = ' '.join(text_raw.split())
    #nlp         = nlp(text)
    #noun_chunks = list(nlp.noun_chunks)
    
    #name            = parser.extract_name(nlp, matcher=matcher)
    #email           = parser.extract_email(text)
    #skills          = parser.extract_skills(nlp, noun_chunks, "skills.csv")
    #edu             = parser.extract_education([sent.string.strip() for sent in nlp.sents])
    #entities        = parser.extract_entity_sections_professional(text_raw)

    insert ={   "uid" : uid,
                "cv" : text,
    #            "name" : name,
    #            "email" : email,
    #            "skills" : skills,
    #            "education" : edu,
    #            "entities" : entities
            }
    
    #user_find = users.find({"uid" : uid}) 
    user_id = users.insert_one(insert)
    
    #if user_find:
    #    user_id = users.update_one( {"uid":uid},{ "$set":{ "cv":text}, "$currentDate":{"lastModified":True} } )
    #    if user_id:
    #        print("update")
    #else:
    #    user_id = users.insert_one(insert)
    #    if user_id:
    #        print("insert")
    
    if user_id:
        print("Success")
        return jsonify({"result" : "success"})
    else:
        print("Unsuccess")
        return jsonify({"result" : "unsuccess"})


if __name__ == '__main__':
    app.run()
