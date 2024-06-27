import nltk
import re
import warnings
import os, time
import jieba

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine, LTTextBox

from elasticsearch import Elasticsearch, helpers
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

warnings.simplefilter("ignore") 

#nltk.download('stopwords')
#nltk.download('punkt') # 

# 引入elasticsearch配置文件
# 安装elasticsearch
# pip install elasticsearch
# 安装elasticsearch-dsl
# pip install elasticsearch-dsl
# 安装elasticsearch-py
# pip install elasticsearch-py
# 安装elasticsearch-py-async
# pip install elasticsearch-py-async
# 安装elasticsearch-py-curator
# pip install elasticsearch-py-curator
# 安装elasticsearch-py-odm
# pip install elasticsearch-py-odm
# 安装elasticsearch-py-odm-async
# pip install elasticsearch-py-odm-async
# 安装elasticsearch-py-odm-curator
# pip install elasticsearch-py-odm-curator
# 安装elasticsearch-py-odm-odm
# pip install elasticsearch-py-odm-odm
# 安装elasticsearch-py-odm-odm-async
# pip install elasticsearch-py-odm-odm-async
# 安装elasticsearch-py-odm-odm-curator
# pip install elasticsearch-py-odm-odm-curator
# 安装elasticsearch-py-odm-odm-odm
# pip install elasticsearch-py-odm-odm-odm

# 安装elasticsearch服务
# docker pull elasticsearch:8.6.0
# docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:8.6.0
# 安装elasticsearch-head插件
# docker run -d --name elasticsearch-head -p 9100:9100 mobz/elasticsearch-head:5
# elasticsearch-head插件访问地址
# http://localhost:9100/
# elasticsearch的官网地址
# https://www.elastic.co/cn/elasticsearch/




ELASTICSEARCH_BASE_URL = os.getenv('ELASTICSEARCH_BASE_URL', 'http://localhost:9200')
ELASTICSEARCH_NAME = os.getenv('ELASTICSEARCH_NAME', 'elastic')
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD', 'changeme')


def extract_text_from_pdf(filename, page_numbers=None, min_line_length=1):
    '''从PDF文件中（按指定页码）提取文本内容'''
    paragrahs = []
    buffer = ''
    full_text = ''

    # 提取全部文本内容
    for i, page_layout in enumerate(extract_pages(filename)):
        # 如果指定了页码，只处理指定页码的内容
        if page_numbers and i not in page_numbers:
            continue
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                full_text += element.get_text() + '\n'

    # 安空行分隔，将文本重新组成段落
    lines = full_text.split('\n')
    for text in lines:
        if len(text) >= min_line_length:
            buffer += (' ' + text) if not text.endswith('-') else text.strip('-')
        elif buffer:
            paragrahs.append(buffer)
            buffer = ''
    if buffer:
        paragrahs.append(buffer)
    return paragrahs


#-----------------关键字检索方法->>>>
def to_keywords(input_string):
    '''（英文）文本只保留关键字'''
    # 使用正则表达式替换所有非字母数字的字符为空格
    no_symbols = re.sub(r'[^a-zA-Z0-9\s]', ' ', input_string)
    word_tokens = word_tokenize(no_symbols)
    # 加载停用词表
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    # 去停用词，取词根
    filtered_sentence = [ps.stem(w)
                         for w in word_tokens if not w.lower() in stop_words]
    return ' '.join(filtered_sentence)

def to_keywords_chinese(input_string):
    """将句子转成检索关键词序列"""
    # 按搜索引擎模式分词
    word_tokens = jieba.cut_for_search(input_string)
    # 加载停用词表
    stop_words = set(stopwords.words('chinese'))
    # 去除停用词
    filtered_sentence = [w for w in word_tokens if not w in stop_words]
    return ' '.join(filtered_sentence)

def sent_tokenize(input_string):
    """按标点断句"""
    # 按标点切分
    sentences = re.split(r'(?<=[。！？；?!])', input_string)
    # 去掉空字符串
    return [sentence for sentence in sentences if sentence.strip()]
#-----------------关键字检索方法-<<<<

#-----------------Elasticsearch方法->>>
def connect_elasticsearch():
    '''连接Elasticsearch'''
    es = Elasticsearch([ELASTICSEARCH_BASE_URL], http_auth=(ELASTICSEARCH_NAME, ELASTICSEARCH_PASSWORD))
    if es.ping():
        print('Connected to Elasticsearch!')
    else:
        print('Could not connect!')
    return es

def create_index(es, index_name = "teacher_demo_index"):
    '''创建索引'''
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, ignore=400)
    print(f'Index {index_name} created!')

def index_document(es, index_name, doc_id, doc_body):
    '''索引文档'''
    es.index(index=index_name, id=doc_id, body=doc_body)
    print(f'Document {doc_id} indexed!')


def search(es, index_name, query_string, top_n=10):
    '''搜索'''
    res = es.search(index=index_name, body={"query": {"match": {"content": query_string}}})
    return res

# 批量索引文档
# Elasticsearch 版本8.6.0之后，不再支持doc_type参数，所以这里不再使用doc_type参数
# index_name: 索引名称
# doc_type: 文档类型 ex: 'doc', 'teacher', 'student', 'course', 'pdf'
# docs: 文档列表，每个文档是一个字典，包含'id'和'content'字段. ex: [{'id': 1, 'content': 'hello world'}, {'id': 2, 'content': 'good morning'}]
def bulk_index(es, index_name, docs):
    '''批量索引文档'''
    actions = []
    for doc in docs:
        action = {
            '_op_type': 'index',
            '_index': index_name,
            '_id': doc['id'],
            '_source': doc
        }
        actions.append(action)
    helpers.bulk(es, actions)
    print(f'{len(docs)} documents indexed!')

def bulk_index_paragrahs(es, index_name, paragrahs):
    '''批量索引文档'''
    actions = [
        {
            "_index": index_name,
            "_source": {
                "keywords": to_keywords_chinese(para),
                "text": para
            }

        } for para in paragrahs
    ]
    helpers.bulk(es, actions)


def delete_index(es, index_name):
    '''删除索引'''
    es.indices.delete(index=index_name)
    print(f'Index {index_name} deleted!')

def delete_document(es, index_name, doc_id):
    '''删除文档'''
    es.delete(index=index_name, id=doc_id)
    print(f'Document {doc_id} deleted!')    

def update_document(es, index_name, doc_id, doc_body):
    '''更新文档'''
    es.update(index=index_name, id=doc_id, body=doc_body)
    print(f'Document {doc_id} updated!')

def get_document(es, index_name, doc_id):
    '''获取文档'''
    res = es.get(index=index_name, id=doc_id)
    return res

def get_all_documents(es, index_name):
    '''获取所有文档'''
    res = es.search(index=index_name, body={"query": {"match_all": {}}})
    return res

def get_all_indices(es):
    '''获取所有索引'''
    res = es.cat.indices()
    return res

def get_mapping(es, index_name):
    '''获取索引映射'''
    res = es.indices.get_mapping(index=index_name)
    return res

def get_settings(es, index_name):
    '''获取索引设置'''
    res = es.indices.get_settings(index=index_name)
    return res

def get_stats(es, index_name):
    '''获取索引统计信息'''
    res = es.indices.stats(index=index_name)
    return res

def get_index(es, index_name):
    '''获取索引信息'''
    res = es.indices.get(index=index_name)
    return res
#-----------------Elasticsearch方法-<<<


#-----------------test functions->>>
def test_extract_text_from_pdf():
    filename = 'sample.pdf'
    paragrahs = extract_text_from_pdf(filename)
    for i, p in enumerate(paragrahs):
        print(f'{i+1}: {p}')

def test_to_keywords():
    input_string = 'Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data.'
    print(to_keywords(input_string))

def test_to_keywords_chinese():
    input_string = '自然语言处理（NLP）是语言学、计算机科学和人工智能的一个子领域，涉及计算机与人类语言之间的交互，特别是如何编程计算机来处理和分析大量的自然语言数据。'
    print(to_keywords_chinese(input_string))

def test_sent_tokenize():
    input_string = 'Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data. NLP is used to apply machine learning algorithms to text and speech.'
    print(sent_tokenize(input_string))  

def test_connect_elasticsearch():
    es = connect_elasticsearch()
    return es

def test_create_index():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')

def test_index_document():
    es = connect_elasticsearch()
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})

def test_search():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})
    res = search(es, index_name='test_index', query_string='world')
    print(res)

def test_bulk_index():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    docs = [{'id': 1, 'content': 'hello world'}, {'id': 2, 'content': 'good morning'}]
    bulk_index(es, index_name='test_index', docs=docs)

def test_bulk_index_pdf():  
    es = connect_elasticsearch()
    create_index(es, index_name='test_index_pdf')
    docs = []
    for i, p in enumerate(extract_text_from_pdf('sample.pdf')):
        docs.append({'id': i, 'content': p})
    bulk_index(es, index_name='test_index_pdf', docs=docs)

def test_bulk_index_paragrahs():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index_paragrahs')
    paragrahs = extract_text_from_pdf('sample.pdf');
    bulk_index_paragrahs(es, index_name='test_index_paragrahs', paragrahs = paragrahs)

def test_delete_index():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    delete_index(es, index_name='test_index')

def test_delete_document():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})
    delete_document(es, index_name='test_index', doc_id=1)

def test_update_document():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})
    update_document(es, index_name='test_index', doc_id=1, doc_body={'doc': {'text': 'good morning'}})

def test_get_document():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})
    res = get_document(es, index_name='test_index', doc_id=1)
    print(res)

def test_get_all_documents():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    index_document(es, index_name='test_index', doc_id=1, doc_body={'text': 'hello world'})
    res = get_all_documents(es, index_name='test_index')
    print(res)

def test_get_all_indices():
    es = connect_elasticsearch()
    res = get_all_indices(es)
    print(res)

def test_get_mapping():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    res = get_mapping(es, index_name='test_index')
    print(res)

def test_get_settings():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    res = get_settings(es, index_name='test_index')
    print(res)

def test_get_stats():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    res = get_stats(es, index_name='test_index')
    print(res)

def test_get_index():
    es = connect_elasticsearch()
    create_index(es, index_name='test_index')
    res = get_index(es, index_name='test_index')
    print(res)

def test_rag_embeddings():
    test_extract_text_from_pdf()
    test_to_keywords()
    test_to_keywords_chinese()
    test_sent_tokenize()
    test_connect_elasticsearch()
    test_create_index()
    test_index_document()
    test_search()
    test_bulk_index()
    #test_delete_index()
    #test_delete_document()
    test_update_document()
    test_get_document()
    test_get_all_documents()
    test_get_all_indices()
    test_get_mapping()
    test_get_settings()
    test_get_stats()
    test_get_index()

#-----------------test functions-<<<


def test_extract_text_from_pdf():
    filename = 'sample.pdf'
    paragrahs = extract_text_from_pdf(filename)
    for i, p in enumerate(paragrahs):
        print(f'{i+1}: {p}')        

if __name__ == '__main__':
    #test_rag_embeddings()
    #test_extract_text_from_pdf()
    #test_bulk_index_pdf()
    test_bulk_index_paragrahs()
    print('All tests passed!')


