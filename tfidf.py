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
from flask import Flask, render_template,request
from flask import jsonify 
from spacy.matcher import Matcher
import spacy
import Parser as parser
import pymongo as pym
from bson.json_util import dumps
from bson.objectid import ObjectId

app = Flask(__name__)

client = pym.MongoClient('mongodb://localhost:27017/')
db = client.test

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
 
def tfidf(n):
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

@app.route('/submitCV')
def submitCV():
    resume = request.args['cv']
    uid = request.args['uid']
    
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)
    
    text_raw    = parser.extract_text('resume.pdf',".pdf")
    text        = ' '.join(text_raw.split())
    nlp         = nlp(text)
    noun_chunks = list(nlp.noun_chunks)
    
    name            = parser.extract_name(nlp, matcher=matcher)
    email           = parser.extract_email(text)
#    mobile          = parser.extract_mobile_number(text)
    skills          = parser.extract_skills(nlp, noun_chunks, "skills.csv")
    edu             = parser.extract_education([sent.string.strip() for sent in nlp.sents])
    entities        = parser.extract_entity_sections_professional(text_raw)
    
    resume_collection=db["CV"]
    insert ={   "uid" : uid,
                "cv" : resume,
                "name" : name,
                "email" : email,
                "skills" : skills,
                "education" : edu,
                "entities" : entities
            }
    resume_collection.insert_one(insert)
    return jsonify()

@app.route('/signup')
def signup():
    usertype = request.args['type']
    fname = request.args['fname']
    lname = request.args['lname']
    number = request.args['number']
    gender = request.args['gender']
    email = request.args['email']
    age = request.args['age']
    password = request.args['password']
    
    
    if usertype == 'Job Seeker':
        db.Collection.insertOne(
            {   fname : fname,
                lname : lname,
                number : number,
                gender : gender,
                email : email,
                age : age,
                password : password
            })
    elif usertype == 'Job Provider':
       db.Collection.insertOne(
            {   fname : fname,
                lname : lname,
                number : number,
                gender : gender,
                email : email,
                age : age,
                password : password
            })
    else:
        print("Invalid")
        

@app.route('/login')
def login():
    uname = request.args['uname']
    password = request.args['password']
    #select

    db.collection.find({ username : uname, password : password })

    
@app.route('/profile')
def profile():
    user_id = request.args['user_id']
    jobde=db["Job_Desc"]

    x = jobde.find({"_id": ObjectId(user_id)})
    
    return dumps(x)


@app.route('/jobpost')
def jobpost():
    job_titl = request.args['job_title']
    job_desc = request.args['job_desc']
    no_cand = request.args['no_cand']
    ##insert

    jobde=db["Job_Desc"]
    insert ={   "job_title" : job_titl,
                "desc" : job_desc,
                "cand" : no_cand
            }
    jobde.insert_one(insert)
    return no_cand
    

@app.route('/recommend')
def recommend():
    job_id = request.args['job_id']
    recommended = tfidf()

@app.route('/allJds')
def allJds():
    uid = request.args['uid']
    #select
    jobde=db["Job_Desc"]

    x = jobde.find({"cand" : "30"})
    
    return dumps(x)

@app.route('/delJd')
def delJd():
    uid = request.args['uid']
    #select
    jobde=db["Job_Description"]

    x = jobde.find({"cand" : "30"})
    
    return dumps(x)

    
    
if __name__ == '__main__':
    app.run()
