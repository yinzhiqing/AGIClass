import json
from pydantic.v1 import BaseModel
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

def show_json(data):
    """用于展示json数据"""
    if isinstance(data, str):
        obj = json.loads(data)
        print(json.dumps(obj, indent=4))
    elif isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=4))
    elif issubclass(type(data), BaseModel):
        print(json.dumps(data.dict(), indent=4, ensure_ascii=False))

def show_list_obj(data):
    """用于展示一组对象"""
    if isinstance(data, list):
        for item in data:
            show_json(item)
    else:
        raise ValueError("Input is not a list")

from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PyMuPDFReader
from llama_index.core import Document
from llama_index.core.node_parser import TokenTextSplitter

def test_read_pdf():
    reader = SimpleDirectoryReader(
            input_dir="./data", # 目标目录
            recursive=False, # 是否递归遍历子目录
            required_exts=[".pdf"], # (可选)只读取指定后缀的文件
            file_extractor = {"pdf": PyMuPDFReader()} # (可选)指定文件类型的读取器
            )
    documents = reader.load_data()


    show_json(documents[0])

    print(documents[0].text)


from llama_index.readers.feishu_docs import FeishuDocsReader
def test_reader_feishu():
    app_id = "cli_a6f1c0fa1fd9d00b"
    app_secret = "dMXCTy8DGaty2xn8I858ZbFDFvcqgiep"

    doc_ids = ["FULadzkWmovlfkxSgLPcE4oWnPf"]

    reader = FeishuDocsReader(
        app_id,
        app_secret,
    )
    documents = reader.load_data(document_ids=doc_ids)
    print(documents[0].text[:1000])
    return documents

from llama_index.core import Document
from llama_index.core.node_parser import TokenTextSplitter

def test_token_text_splitter():
    node_parser = TokenTextSplitter(
         chunk_size=100,
         chunk_overlap=50
    )

    documents = test_reader_feishu()
    nodes = node_parser.get_nodes_from_documents(
            documents, 
            show_progress=False
    )
    show_json(nodes[0])
    show_json(nodes[1])

from llama_index.readers.file import FlatReader
from llama_index.core.node_parser import MarkdownNodeParser
from pathlib import Path

def test_markdown_node_parser():
    md_docs = FlatReader().load_data(Path("./data/ChatALL.md"))
    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents(md_docs)

    show_json(nodes[0])
    show_json(nodes[1])

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.readers.file import PyMuPDFReader
import os
def test_index():
    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"]
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()

    # 定义文档分块器
    node_parser = TokenTextSplitter(chunk_size=300, chunk_overlap=100)

    # 切换文档
    nodes = node_parser.get_nodes_from_documents(documents)

    # 构建索引
    index = VectorStoreIndex(nodes)

    # 获取 retriever
    retriever = index.as_retriever(similarity_top_k=2)

    # 搜索
    results = retriever.retrieve("Llama2有多少参数")

    show_list_obj(results)


import os
import chromadb
from chromadb.config import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext


def test_index_chroma():
    if os.environ.get("CUR_ENV_IS_STUDENT", 'false') == 'true':
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

    # 读取文档
    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"]
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()

    # 定义文档分块器
    node_parser = TokenTextSplitter(chunk_size=100, chunk_overlap=20)

    # 切割文档
    nodes = node_parser.get_nodes_from_documents(documents)

    # 创建chroma客户端
    chroma_client = chromadb.EphemeralClient(settings=Settings(allow_reset=True))
    chroma_client.reset()
    chroma_collection = chroma_client.create_collection("demo")

    # 保存文档
    vector_store = ChromaVectorStore(chroma_collection = chroma_collection)

    # 创建存储上下文
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 构建索引
    index = VectorStoreIndex(nodes, storage_context = storage_context)

    # 获取 retriever
    vector_retriever = index.as_retriever(similarity_top_k=3)

    # 搜索
    results = vector_retriever.retrieve("Llama2有多少参数")

    # 展示结果
    show_list_obj(results)

    return results

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import VectorStoreIndex
from llama_index.core import VectorStoreIndex
from llama_index.readers.file import PyMuPDFReader
from llama_index.core.postprocessor import SentenceTransformerRerank


import time
class Timer:
    def __init__(self):
        self.start_time = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        print(f"Time elapsed: {self.end_time - self.start_time} s")

def test_pipleline():
    # 创建chroma客户端
    chroma_client = chromadb.EphemeralClient(settings=Settings(allow_reset=True))
    chroma_client.reset()
    chroma_collection = chroma_client.create_collection("ingestion_demo")

    vector_store = ChromaVectorStore(chroma_collection = chroma_collection)
   
    pipeline = IngestionPipeline(
            transformations = [
                SentenceSplitter(chunk_size=300, chunk_overlap=100),
                TitleExtractor(),
                OpenAIEmbedding(),
            ],
            vector_store = vector_store
    )

    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"],
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()


    # 计时
    with Timer():
        pipeline.run(documents=documents)

    # 保存pipeline
    pipeline.persist("./pipeline_storage")

    index = VectorStoreIndex.from_vector_store(vector_store)

    vector_retriever = index.as_retriever(similarity_top_k=1)

    results = vector_retriever.retrieve("Llama2有多少参数")


    show_list_obj(results)

def test_pipeline_cache():
    # 创建chroma客户端
    chroma_client = chromadb.EphemeralClient(settings=Settings(allow_reset=True))
    chroma_client.reset()
    chroma_collection = chroma_client.create_collection("ingestion_demo")

    vector_store = ChromaVectorStore(chroma_collection = chroma_collection)

    pipeline = IngestionPipeline(
            transformations = [
                SentenceSplitter(chunk_size=300, chunk_overlap=100),
                TitleExtractor(),
                OpenAIEmbedding(),
            ],
            vector_store = vector_store
    )

    pipeline.load("./pipeline_storage")

    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"],
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()

    # 计时
    with Timer():
        pipeline.run(documents=documents)

    index = VectorStoreIndex.from_vector_store(vector_store)

    vector_retriever = index.as_retriever(similarity_top_k=5)

    nodes = vector_retriever.retrieve("Llama2 能商用吗")

    for i, node in enumerate(nodes):
        print(f"[{i}]{node.text}")

    # 后处理 !!!需要机器性能好，容易死机
    #postprocessor = SentenceTransformerRerank(
    #        model = "BAAI/bge-reranker-large", top_n=2
    #)

    #nodes = postprocessor.postprocess_nodes(nodes, query_str="Llama2 能商用吗")
    #print("sort>>>>>>>>>>>>>>>>>")
    #for i, node in enumerate(nodes):
    #    print(f"[{i}]{node.text}")

    stream = True
    respones = None
    if stream:
        qa_engine = index.as_query_engine(streaming = True)
        respones = qa_engine.query("Llama2 有多少参数")
        respones.print_response_stream()
    else:
        qa_engine = index.as_query_engine()
        respones = qa_engine.query("Llama2 有多少参数")
        print(respones)
    print("\n")

    
def test_mult_chat():
    # 创建chroma客户端
    chroma_client = chromadb.EphemeralClient(settings=Settings(allow_reset=True))
    chroma_client.reset()
    chroma_collection = chroma_client.create_collection("ingestion_demo")

    vector_store = ChromaVectorStore(chroma_collection = chroma_collection)

    pipeline = IngestionPipeline(
            transformations = [
                SentenceSplitter(chunk_size=300, chunk_overlap=100),
                TitleExtractor(),
                OpenAIEmbedding(),
            ],
            vector_store = vector_store
    )

    pipeline.load("./pipeline_storage")

    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"],
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()

    # 计时
    with Timer():
        pipeline.run(documents=documents)

    index = VectorStoreIndex.from_vector_store(vector_store)

    chat_engine = index.as_chat_engine()
    respones = chat_engine.query("Llama2 有多少参数")
    print(respones)

    respones = chat_engine.query("How many at most?")
    print(respones)
    print("\n")

    
from llama_index.core import PromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import ChatPromptTemplate


def test_propt_template():

    chat_text_qa_msgs = [
            ChatMessage(
                role = MessageRole.SYSTEM,
                content="你叫{name}, 你必须根据用户提供的上下文回答问题。",
                ),
            ChatMessage(
                role = MessageRole.USER,
                content=(
                    "已知上下文：\n" \
                    "{context}\n\n" \
                    "问题：{question}"    
                    )
                ),
            ]
    
    text_qa_template = ChatPromptTemplate(chat_text_qa_msgs)
    print(text_qa_template.format(
        name="呱呱", 
        context="这是一个测试",
        question="这是什么"
        )
    ) 

from llama_index.llms.openai import OpenAI

def test_llms():
    llm = OpenAI(temperature=0, model="gpt-4o")
    prompt = PromptTemplate(" 写一个关于{topic}的笑话")

    #response = llm.complete(prompt.format(topic="小明"))
    #print(response.text)

    chat_text_qa_msgs = [
            ChatMessage(
                role = MessageRole.SYSTEM,
                content="你叫{name}, 你必须根据用户提供的上下文回答问题。",
                ),
            ChatMessage(
                role = MessageRole.USER,
                content=(
                    "已知上下文：\n" \
                    "{context}\n\n" \
                    "问题：{question}"    
                    )
                ),
            ]
    text_qa_template = ChatPromptTemplate(chat_text_qa_msgs)
    response = llm.complete(
            text_qa_template.format(
                name="呱呱", 
                context="这是一个测试",
                question="你是谁，我们在干嘛"
                )
            )
    print(response.text)

# 设置全局使用的语言模型
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
# 语言模型
#Settings.llm = OpenAI(temperature=0, model="gpt-4o")
# 词向量模型
#Setting.embed_model = OpenAIEmbedding(model="text-embedding-3-small", dimension=512)

def client():
    import chromadb
    import time
    from llama_index.core import VectorStoreIndex, KeywordTableIndex, SimpleDirectoryReader
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.core.ingestion import IngestionPipeline
    from llama_index.readers.file import PyMuPDFReader
    from llama_index.core import Settings
    from llama_index.core import StorageContext
    from llama_index.core.postprocessor import SentenceTransformerRerank
    from llama_index.core.retrievers import QueryFusionRetriever
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.chat_engine import CondenseQuestionChatEngine
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding


    chroma_client = chromadb.PersistentClient(path="./data")

    # 指定全局llm和embedding模型
    Settings.llm = OpenAI(temperature=0, model="gpt-4o")
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", dimension=512)

    # 指定全局文档处理的 Ingestion Pipeline
    Setting.transformations = [SentenceSplitter(chunk_size=300, chunk_overlap=100)]

    # 加载本地文档
    documents = SimpleDirectoryReader(
        "./data",
        required_exts=[".pdf"],
        #file_extractor={".pdf": PyMuPDFReader()}
    ).load_data()

    # 创建 collection
    collection_name = hex(int(time.time()))
    chroma_collection = chroma_client.get_or_create_collection(collection_name)

    # 创建 vector store
    vector_store = ChromaVectorStore(chroma_collection = chroma_collection)

    # 指定Vector Store的Storage用于index
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    # 定义检索后排序模型
    reranker = SentenceTransformerRerank(model = "BAAI/bge-reranker-large", top_n=2)

    # 定义 RAG Fusion检索器
    fusion_retriever = QueryFusionRetriever(
        [index.as_retriever()],
        similarity_top_k=3, # 检索召回top k 结果
        num_queries=3, # 每次检索的query数量
        use_async=True
        # query_gen_prompt = "..." # 自定义query生成模板
    )

    # 构建单轮query engine
    query_engine = RetrieverQueryEngine.from_args(
        fusion_retriever,
        node_postprocessors = [reranker]
    )

    # 对话引擎
    chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=query_engine,
            # condense_question_prompt = "..." # 可以自定义chat message prompt 模板
    )

    while True:
        question = input("User: ")
        if question.strip() == "":
            break

        response = chat_engine.chat(question)
        print(f"AI: {response}")


# 入口
if __name__ == "__main__":
    #test_read_pdf()
    #test_reader_feishu()
    #test_token_text_splitter()
    # test_markdown_node_parser()
    #test_index()
    #test_index_chroma()
    #test_pipleline()
    #test_pipeline_cache()
    #test_mult_chat()
    #test_propt_template()
    test_llms()
