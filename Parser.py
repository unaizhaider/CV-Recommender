import io
import re
import nltk
import pandas as pd
#import docx2txt
from datetime import datetime
from dateutil import relativedelta
from spacy.matcher import Matcher
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


NAME_PATTERN      = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

EDUCATION         = [
                    'BE','B.E.', 'B.E', 'BS', 'B.S', 'ME', 'M.E', 'M.E.', 'MS', 'M.S', 'BTECH', 'MTECH', 
                    'SSC', 'HSC', 'CBSE', 'ICSE', 'X', 'XII'
                    ]

NOT_ALPHA_NUMERIC = r'[^a-zA-Z\d]'

NUMBER            = r'\d+'

MONTHS_SHORT      = r'(jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec)'
MONTHS_LONG       = r'(january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december)'
MONTH             = r'(' + MONTHS_SHORT + r'|' + MONTHS_LONG + r')'
YEAR              = r'(((20|19)(\d{2})))'

STOPWORDS         = set(stopwords.words('english'))

RESUME_SECTIONS_PROFESSIONAL = [
                    'experience',
                    'education',
                    'interests',
                    'professional experience',
                    'publications',
                    'skills',
                    'certifications',
                    'objective',
                    'career objective',
                    'summary',
                    'coursework',
                    'leadership'
                ]

RESUME_SECTIONS_GRAD = [
                    'accomplishments',
                    'experience',
                    'education',
                    'interests',
                    'projects',
                    'professional experience',
                    'publications',
                    'skills',
                    'certifications',
                    'objective',
                    'career objective',
                    'summary',
                    'coursework',
                    'leadership'
                ]

COMPETENCIES = {
    'teamwork': [
        'supervised',
        'facilitated',
        'planned',
        'plan',
        'served',
        'serve',
        'project lead',
        'managing',
        'managed',
        'lead ',
        'project team',
        'team',
        'conducted',
        'worked',
        'gathered',
        'organized',
        'mentored',
        'assist',
        'review',
        'help',
        'involve',
        'share',
        'support',
        'coordinate',
        'cooperate',
        'contributed'
    ],
    'communication': [
        'addressed',
        'collaborated',
        'conveyed',
        'enlivened',
        'instructed',
        'performed',
        'presented',
        'spoke',
        'trained',
        'author',
        'communicate',
        'define',
        'influence',
        'negotiated',
        'outline',
        'proposed',
        'persuaded',
        'edit',
        'interviewed',
        'summarize',
        'translate',
        'write',
        'wrote',
        'project plan',
        'business case',
        'proposal',
        'writeup'
    ],
    'analytical': [
        'process improvement',
        'competitive analysis',
        'aligned',
        'strategive planning',
        'cost savings',
        'researched ',
        'identified',
        'created',
        'led',
        'measure',
        'program',
        'quantify',
        'forecasr',
        'estimate',
        'analyzed',
        'survey',
        'reduced',
        'cut cost',
        'conserved',
        'budget',
        'balanced',
        'allocate',
        'adjust',
        'lauched',
        'hired',
        'spedup',
        'speedup',
        'ran',
        'run',
        'enchanced',
        'developed'
    ],
    'result_driven': [
        'cut',
        'decrease',
        'eliminate',
        'increase',
        'lower',
        'maximize',
        'rasie',
        'reduce',
        'accelerate',
        'accomplish',
        'advance',
        'boost',
        'change',
        'improve',
        'saved',
        'save',
        'solve',
        'solved',
        'upgrade',
        'fix',
        'fixed',
        'correct',
        'achieve'           
    ],
    'leadership': [
        'advise',
        'coach',
        'guide',
        'influence',
        'inspire',
        'instruct',
        'teach',
        'authorized',
        'chair',
        'control',
        'establish',
        'execute',
        'hire',
        'multi-task',
        'oversee',
        'navigate',
        'prioritize',
        'approve',
        'administer',
        'preside',
        'enforce',
        'delegate',
        'coordinate',
        'streamlined',
        'produce',
        'review',
        'supervise',
        'terminate',
        'found',
        'set up',
        'spearhead',
        'originate',
        'innovate',
        'implement',
        'design',
        'launch',
        'pioneer',
        'institute'
    ]
}

MEASURABLE_RESULTS = {
    'metrics': [
        'saved',
        'increased',
        '$ ',
        '%',
        'percent',
        'upgraded',
        'fundraised ',
        'millions',
        'thousands',
        'hundreds',
        'reduced annual expenses ',
        'profits',
        'growth',
        'sales',
        'volume',
        'revenue',
        'reduce cost',
        'cut cost',
        'forecast',
        'increase in page views',
        'user engagement',
        'donations',
        'number of cases closed',
        'customer ratings',
        'client retention',
        'tickets closed',
        'response time',
        'average',
        'reduced customer complaints',
        'managed budget',
        'numeric_value'
    ],
    'action_words': [
        'developed',
        'led',
        'analyzed',
        'collaborated',
        'conducted',
        'performed',
        'recruited',
        'improved',
        'founded',
        'transformed',
        'composed',
        'conceived',
        'designed',
        'devised',
        'established',
        'generated',
        'implemented',
        'initiated',
        'instituted',
        'introduced',
        'launched',
        'opened',
        'originated',
        'pioneered',
        'planned',
        'prepared',
        'produced',
        'promoted',
        'started',
        'released',
        'administered',
        'assigned',
        'chaired',
        'consolidated',
        'contracted',
        'co-ordinated',
        'delegated',
        'directed',
        'evaluated',
        'executed',
        'organized',
        'oversaw',
        'prioritized',
        'recommended',
        'reorganized',
        'reviewed',
        'scheduled',
        'supervised',
        'guided',
        'advised',
        'coached',
        'demonstrated',
        'illustrated',
        'presented',
        'taught',
        'trained',
        'mentored',
        'spearheaded',
        'authored',
        'accelerated',
        'achieved',
        'allocated',
        'completed',
        'awarded',
        'persuaded',
        'revamped',
        'influenced',
        'assessed',
        'clarified',
        'counseled',
        'diagnosed',
        'educated',
        'facilitated',
        'familiarized',
        'motivated',
        'participated',
        'provided',
        'referred',
        'rehabilitated',
        'reinforced',
        'represented',
        'moderated',
        'verified',
        'adapted',
        'coordinated',
        'enabled',
        'encouraged',
        'explained',
        'informed',
        'instructed',
        'lectured',
        'stimulated',
        'classified',
        'collated',
        'defined',
        'forecasted',
        'identified',
        'interviewed',
        'investigated',
        'researched',
        'tested',
        'traced',
        'interpreted',
        'uncovered',
        'collected',
        'critiqued',
        'examined',
        'extracted',
        'inspected',
        'inspired',
        'summarized',
        'surveyed',
        'systemized',
        'arranged',
        'budgeted',
        'controlled',
        'eliminated',
        'itemised',
        'modernised',
        'operated',
        'organised',
        'processed',
        'redesigned',
        'reduced',
        'refined',
        'resolved',
        'revised',
        'simplified',
        'solved',
        'streamlined',
        'appraised',
        'audited',
        'balanced',
        'calculated',
        'computed',
        'projected',
        'restructured',
        'modelled',
        'customized',
        'fashioned',
        'integrated',
        'proved',
        'revitalized',
        'set up',
        'shaped',
        'structured',
        'tabulated',
        'validated',
        'approved',
        'catalogued',
        'compiled',
        'dispatched',
        'filed',
        'monitored',
        'ordered',
        'purchased',
        'recorded',
        'retrieved',
        'screened',
        'specified',
        'systematized',
        'conceptualized',
        'brainstomed',
        'tasked',
        'supported',
        'proposed',
        'boosted',
        'earned',
        'negotiated',
        'navigated',
        'updated',
        'utilized'
    ],
    'weak_words': [
        'i',
        'got',
        'i\'ve',
        'because',
        'our',
        'me',
        'he',
        'her',
        'him',
        'she',
        'helped',
        'familiar',
        'asssisted',
        'like',
        'enjoy',
        'love',
        'did',
        'tried',
        'attempted',
        'worked',
        'approximately',
        'managed',
        'manage',
        'create',
        'created'
    ]
}
def extract_text_from_pdf(pdf_path):
    
    if not isinstance(pdf_path, io.BytesIO):
        with open(pdf_path, 'rb') as fh:
            try:
                for page in PDFPage.get_pages(fh, 
                                            caching=True,
                                            check_extractable=True):
                    resource_manager = PDFResourceManager()
                    fake_file_handle = io.StringIO()
                    converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
                    page_interpreter = PDFPageInterpreter(resource_manager, converter)
                    page_interpreter.process_page(page)
        
                    text = fake_file_handle.getvalue()
                    yield text
        
                    converter.close()
                    fake_file_handle.close()
            except PDFSyntaxError:
                return
    else:
        try:
            for page in PDFPage.get_pages(pdf_path, 
                                            caching=True,
                                            check_extractable=True):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
                page_interpreter = PDFPageInterpreter(resource_manager, converter)
                page_interpreter.process_page(page)
    
                text = fake_file_handle.getvalue()
                yield text
    
                converter.close()
                fake_file_handle.close()
        except PDFSyntaxError:
            return


def extract_text(file_path, extension):
    
    text = ''
    if extension == '.pdf':
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page
    return text

def extract_entity_sections_grad(text):
   
    text_split = [i.strip() for i in text.split('\n')]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(RESUME_SECTIONS_GRAD)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in RESUME_SECTIONS_GRAD:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)
    
    return entities

def extract_entities_wih_custom_model(custom_nlp_text):
    
    entities  = {}
    for ent in custom_nlp_text.ents:
        if ent.label_ not in entities.keys():
            entities[ent.label_] = [ent.text]
        else:
            entities[ent.label_].append(ent.text)
    for key in entities.keys():
        entities[key] = list(set(entities[key]))
    return entities

def get_total_experience(experience_list):
   
    exp_ = []
    for line in experience_list:
        experience = re.search('(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present)', line, re.I)
        if experience:
            exp_.append(experience.groups())
    total_experience_in_months = sum([get_number_of_months_from_dates(i[0], i[2]) for i in exp_])
    return total_experience_in_months

def get_number_of_months_from_dates(date1, date2):
    
    if date2.lower() == 'present':
        date2 = datetime.now().strftime('%b %Y')
    try:
        if len(date1.split()[0]) > 3:
            date1 = date1.split()
            date1 = date1[0][:3] + ' ' + date1[1] 
        if len(date2.split()[0]) > 3:
            date2 = date2.split()
            date2 = date2[0][:3] + ' ' + date2[1]
    except IndexError:
        return 0
    try: 
        date1 = datetime.strptime(str(date1), '%b %Y')
        date2 = datetime.strptime(str(date2), '%b %Y')
        months_of_experience = relativedelta.relativedelta(date2, date1)
        months_of_experience = months_of_experience.years * 12 + months_of_experience.months
    except ValueError:
        return 0
    return months_of_experience

def extract_entity_sections_professional(text):
    
    text_split = [i.strip() for i in text.split('\n')]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(RESUME_SECTIONS_PROFESSIONAL)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in RESUME_SECTIONS_PROFESSIONAL:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)
    return entities

def extract_email(text):
    
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None

def extract_name(nlp_text, matcher):
   
    pattern = [NAME_PATTERN]
    
    matcher.add('NAME', None, *pattern)
    
    matches = matcher(nlp_text)
    
    for _, start, end in matches:
        span = nlp_text[start:end]
        if 'name' not in span.text.lower():
            return span.text

def extract_mobile_number(text):
    
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{7})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        else:
            return number

def extract_skills(nlp_text, noun_chunks, skills_file=None):
   
    tokens = [token.text for token in nlp_text if not token.is_stop]
   
    data = pd.read_csv(skills_file)
    skills = list(data.columns.values)
    skillset = []
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    return [i.capitalize() for i in set([i.lower() for i in skillset])]

def cleanup(token, lower = True):
    if lower:
       token = token.lower()
    return token.strip()

def extract_education(nlp_text):
    
    edu = {}

    try:
        for index, text in enumerate(nlp_text):
            for tex in text.split():
                tex = re.sub(r'[?|$|.|!|,]', r'', tex)
                if tex.upper() in EDUCATION and tex not in STOPWORDS:
                    edu[tex] = text + nlp_text[index + 1]
    except IndexError:
        pass

    education = []
    for key in edu.keys():
        year = re.search(re.compile(YEAR), edu[key])
        if year:
            education.append((key, ''.join(year.group(0))))
        else:
            education.append(key)
    return education

def extract_experience(resume_text):
    
    wordnet_lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))

    word_tokens = nltk.word_tokenize(resume_text)

    filtered_sentence = [w for w in word_tokens if not w in stop_words and wordnet_lemmatizer.lemmatize(w) not in stop_words] 
    sent = nltk.pos_tag(filtered_sentence)

    cp = nltk.RegexpParser('P: {<NNP>+}')
    cs = cp.parse(sent)
    
    test = []
    
    for vp in list(cs.subtrees(filter=lambda x: x.label()=='P')):
        test.append(" ".join([i[0] for i in vp.leaves() if len(vp.leaves()) >= 2]))

    x = [x[x.lower().index('experience') + 10:] for i, x in enumerate(test) if x and 'experience' in x.lower()]
    return x
