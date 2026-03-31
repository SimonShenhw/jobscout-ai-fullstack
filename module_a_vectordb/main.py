from fastapi import FastAPI
from pydantic import BaseModel
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# [ZH] 1. 启动 FastAPI
# [EN] 1. Initialize FastAPI
app = FastAPI(title="Module A: Vector DB API - Resume Tips")

# [ZH] 2. 连接本地持久化向量数据库
# [EN] 2. Connect to local persistent vector database
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory="./chroma_data", embedding_function=embedding_function)


# [ZH] 3. 包装为 LangChain @tool，方便其他 Agent 调用
# [EN] 3. Wrap as LangChain @tool for inter-agent invocation
@tool
def retrieve_resume_tips(query: str) -> str:
    """Useful for retrieving tech resume tips and interview strategies."""
    docs = db.similarity_search(query, k=2)
    return "\n\n".join([doc.page_content for doc in docs])


# [ZH] 4. 定义接收的数据格式
# [EN] 4. Define request data schema
class SearchQuery(BaseModel):
    query: str


# [ZH] 5. 开放对外的搜索接口
# [EN] 5. Expose public search endpoint
@app.post("/api/v1/search")
async def search_vector_db(request: SearchQuery):
    result = retrieve_resume_tips.invoke({"query": request.query})
    return {"status": "success", "result": result}


# [ZH] 6. 健康检查端点
# [EN] 6. Health check endpoint
@app.get("/health", tags=["Ops"])
async def health():
    return {"status": "ok", "module": "vectordb", "version": "1.0.0"}
