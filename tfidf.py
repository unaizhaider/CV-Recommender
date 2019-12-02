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
resume=db["CV_att"]


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
 
def tfidf():
    mypath='F:/Taha/resume-parser-master/resume' #path where resumes are saved
    onlyfiles = [os.path.join(mypath, f) for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
 
    i = 0 
    dat = []
    while i < len(onlyfiles):
        file = onlyfiles[i]
        text = extract_text_from_pdf(file)
        dat.append(text)
        i +=1
        
    raw_documents = dat
    
    cor = []
    for i in range(0, 6):
        review = re.sub('[^a-zA-Z0-9]', ' ', raw_documents[i])
        review = review.lower()
        review = review.split()
        #ps = PorterStemmer()
        lm = WordNetLemmatizer()
        review = [lm.lemmatize(word) for word in review if not word in set(stopwords.words('english'))]
        review = ' '.join(review)
        cor.append(review)
    gen_docs = [[w.lower() for w in word_tokenize(text)] 
                for text in cor]
    
    dictionary = gensim.corpora.Dictionary(gen_docs)
    
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    
    tf_idf = gensim.models.TfidfModel(corpus)
    
    sims = gensim.similarities.Similarity('F:/Similarity/sims',tf_idf[corpus],
                                          num_features=len(dictionary))
    
    with open("JobDescription.txt") as f:
        file_content = f.read().rstrip("\n")
    
    file_content = re.sub('[^a-zA-Z0-9]', ' ', file_content)
    file_content = file_content.lower()
    file_content = file_content.split()
    #ps = PorterStemmer()
    lm = WordNetLemmatizer()
    file_content = [lm.lemmatize(word) for word in file_content if not word in set(stopwords.words('english'))]
    file_content = ' '.join(file_content)
    query_doc = [file_content.lower() for file_content in word_tokenize(file_content)]
    query_doc_bow = dictionary.doc2bow(query_doc)
    query_doc_tf_idf = tf_idf[query_doc_bow]
    
    x=sims[query_doc_tf_idf]
    
    return x

@app.route('/')
def index():
    return "Hello"

@app.route('/test',methods=['POST'])
@cross_origin(supports_credentials=True)
def test():
    users = Job_Seeker
    req=request.get_json(force=True)
    uname = req['username']
    password = req['password']
    user_id = users.insert_one(
            {   "job_title" : uname,
                
            })
    x=str(user_id.inserted_id)
    #result = {'job title': jobtitle + ' registered'}
    if user_id:
        result = {   "job_title" : uname,
                      "id" : x
                     # "job_id" : user_id.inserted_id
                }
    return jsonify({'result' : result})
 
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
    

@app.route('/recommend',methods=['POST'])
@cross_origin(supports_credentials=True)
def recommend():
    req=request.get_json(force=True)
    req2=request.headers['Authorization']
    x = list(Job_Description.find({},{"jpid" : req2}))
    
    #recommended = tfidf(x[0])
    

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
    cv = request.files['file']
    uid=request.headers['Authorization']
    users = resume
    print(cv.filename)
    #print(cv.read())
    print(uid)
    #nlp = spacy.load('en_core_web_sm')
    #matcher = Matcher(nlp.vocab)
    
    #text = extract_text_from_pdf(cv)
    #text_raw    = parser.extract_text(cv,".pdf")
    #text        = ' '.join(text_raw.split())
    #nlp         = nlp(text)
    #noun_chunks = list(nlp.noun_chunks)
    
    #name            = parser.extract_name(nlp, matcher=matcher)
    #email           = parser.extract_email(text)
    #skills          = parser.extract_skills(nlp, noun_chunks, "skills.csv")
    #edu             = parser.extract_education([sent.string.strip() for sent in nlp.sents])
    #entities        = parser.extract_entity_sections_professional(text_raw)

    #insert ={   "uid" : uid,
    #            "cv" : resume,
    #            "name" : name,
    #            "email" : email,
    #            "skills" : skills,
    #            "education" : edu,
    #            "entities" : entities
    #        }
    #user_id = users.insert_one(insert)
    #if user_id:
     #   return jsonify({"result" : "success"})
    #else:
    return jsonify({"result" : "unsuccess"})

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def fileUpload():
    target=os.path.join(UPLOAD_FOLDER,'test_docs')
    if not os.path.isdir(target):
        os.mkdir(target)
    file = request.files['file'] 
    filename = secure_filename(file.filename)
    destination="/".join([target, filename])
    file.save(destination)
    session['uploadFilePath']=destination
    response="Whatever you wish too return"
    return response


    
if __name__ == '__main__':
    app.run()
