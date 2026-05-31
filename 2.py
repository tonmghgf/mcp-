# ==============================
# 1. 安装依赖（只需一次）
# ==============================
# pip install langchain langchain-community langchain-huggingface
# pip install pypdf sentence-transformers faiss-cpu

# ==============================
# 2. 导入库
# ==============================
# 文档加载
from langchain_community.document_loaders import PyPDFLoader

# 文本切分（新版）
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 向量库
from langchain_community.vectorstores import FAISS

# embedding
from langchain_huggingface import HuggingFaceEmbeddings
import re
import os

# ==============================
# 3. 读取多个PDF
# ==============================
def load_pdfs(pdf_paths):
    docs = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        docs.extend(loader.load())
    return docs

# ==============================
# 4. 文本清洗（重点！）
# ==============================
def clean_text(text):
    text = re.sub(r'\n+', '\n', text)  # 多余换行
    text = re.sub(r'\s+', ' ', text)   # 多空格
    text = re.sub(r'Page \d+', '', text)  # 去页码
    text = text.strip()
    return text

def clean_docs(docs):
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    return docs

# ==============================
# 5. 文本切块
# ==============================
def split_docs(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(docs)
    return chunks

# ==============================
# 6. 向量化模型
# ==============================
def load_embedding():
    embedding = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5"  # 推荐直接用在线模型名
    )
    return embedding

# ==============================
# 7. 构建向量库
# ==============================
def build_vector_db(chunks, embedding, save_path="faiss_db"):
    db = FAISS.from_documents(chunks, embedding)
    db.save_local(save_path)
    return db

# ==============================
# 8. 加载向量库（下次不用重新处理）
# ==============================
def load_vector_db(embedding, save_path="faiss_db"):
    db = FAISS.load_local(save_path, embedding, allow_dangerous_deserialization=True)
    return db

# ==============================
# 9. 主流程
# ==============================
if __name__ == "__main__":
    pdf_files = [
        "金融知识1.pdf",
        "金融知识2.pdf"
    ]

    print("📥 加载PDF...")
    docs = load_pdfs(pdf_files)

    print("🧹 清洗文本...")
    docs = clean_docs(docs)

    print("✂️ 切块...")
    chunks = split_docs(docs)

    print(f"📊 共生成 {len(chunks)} 个文本块")

    print("🧠 加载Embedding模型...")
    embedding = load_embedding()

    print("💾 构建向量数据库...")
    db = build_vector_db(chunks, embedding)

    print("✅ 向量库构建完成！")