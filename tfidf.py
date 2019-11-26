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
app = Flask(__name__)



mypath='F:/Taha/resume-parser-master/resume' #path where resumes are saved
onlyfiles = [os.path.join(mypath, f) for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
 
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
    return render_template("index.html")

@app.route('/submitCV')
def submitCV():
    

if __name__ == '__main__':
    app.run()
