from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# [ZH] 1. 读取简历建议文本文件
# [EN] 1. Load resume tips text file
print("1. 正在读取 resume_tips.txt / Loading resume_tips.txt...")
loader = TextLoader("resume_tips.txt", encoding="utf-8")
documents = loader.load()

# [ZH] 2. 将文本切割为小块，便于向量化检索
#      chunk_size=350 让每条 tip（约 200-300 字符）保持完整，overlap=50 保证上下文连贯
# [EN] 2. Split text into chunks. chunk_size=350 keeps each tip (~200-300 chars) intact;
#      overlap=50 preserves context between chunks
print("2. 正在切割文本 / Splitting text into chunks...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=350, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# [ZH] 3. 使用 SentenceTransformer 生成向量，存入 ChromaDB
# [EN] 3. Generate embeddings with SentenceTransformer, persist to ChromaDB
print("3. 正在转换向量并存入数据库 / Generating embeddings and building vector DB...")
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# [ZH] 数据将保存在当前目录下的 chroma_data 文件夹中
# [EN] Data will be persisted to ./chroma_data directory
db = Chroma.from_documents(docs, embedding_function, persist_directory="./chroma_data")

print("[OK] Done! Database has been built successfully. / 数据库构建完成！")
