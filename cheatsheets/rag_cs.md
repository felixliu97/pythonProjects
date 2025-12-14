# Rag Cheatsheet

===============================================
This file serves as a reference for building RAG pipelines using Python.
Primary libraries assumed: LangChain, OpenAI, ChromaDB/FAISS.

Sections:
1. Setup & Imports
2. Document Loading
3. Text Splitting
4. Embeddings
5. Vector Stores
6. Retrieval
7. Generation (LLM)
8. Full Pipeline Example

## 1. SETUP & IMPORTS

``` python
import os
from typing import List

# pip install langchain langchain-openai chromadb faiss-cpu pypdf tiktoken

from langchain_community.document_loaders import TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Set API Key
# os.environ["OPENAI_API_KEY"] = "sk-..."
```

## 2. DOCUMENT LOADING

``` python
def load_documents():
    """
    Examples of loading different document types.

    """
    # Text File
    loader_txt = TextLoader("./data/sample.txt")
    docs_txt = loader_txt.load()
    
    # PDF File
    loader_pdf = PyPDFLoader("./data/sample.pdf")
    docs_pdf = loader_pdf.load()
    
    # Web Page
    loader_web = WebBaseLoader("https://example.com")
    docs_web = loader_web.load()
    
    return docs_txt + docs_pdf + docs_web
```

## 3. TEXT SPLITTING (CHUNKING)

``` python
def split_text(documents):
    """
        RecursiveCharacterTextSplitter is generally recommended for text.

    """
    # Recursive Splitter (Tries to split by paragraph, then newline, then space)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Characters per chunk
        chunk_overlap=200,    # Overlap to maintain context between chunks
        separators=["\n\n", "\n", " ", ""]
    )
    
    splits = text_splitter.split_documents(documents)
    return splits
```

## 4. EMBEDDINGS

``` python
def get_embeddings_model():
    """
    Initialize the embedding model.

    """
    # OpenAI Embeddings (ada-002 or v3-small)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Alternative: HuggingFace (Local)
    # from langchain_community.embeddings import HuggingFaceEmbeddings
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    return embeddings
```

## 5. VECTOR STORES

``` python
def create_vector_store(splits, embeddings):
    """
    Create a vector store from document splits.

    """
    # ChromaDB (Persistent)
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    # FAISS (In-memory / Local)
    # vectorstore = FAISS.from_documents(splits, embeddings)
    
    return vectorstore
```

## 6. RETRIEVAL

``` python
def get_retriever(vectorstore):
    """
    Configure the retriever.

    """
    # Basic Similarity Search
    # k: Number of documents to return
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    
    # MMR (Maximal Marginal Relevance) - Balances relevance and diversity
    # retriever = vectorstore.as_retriever(
    #     search_type="mmr",
    #     search_kwargs={"k": 4, "fetch_k": 20, "lambda_mult": 0.5}
    # )
    
    return retriever
```

## 7. GENERATION (LLM & CHAIN)

``` python
def create_rag_chain(retriever):
    """
    Create the RAG chain combining retrieval and generation.

    """
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Define Prompt Template
    template = """Answer the question based only on the following context:
    {context}
    
    Question: {question}
    """

    # Helper to format documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Construct the Chain (LCEL - LangChain Expression Language)
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
```

## 8. FULL PIPELINE EXAMPLE

``` python
def main():
    # 1. Load
    # docs = load_documents() # Assuming files exist
    # For demo, creating dummy doc
    from langchain_core.documents import Document
    docs = [Document(page_content="RAG stands for Retrieval-Augmented Generation. It combines retrieval with LLMs.")]

    # 2. Split
    splits = split_text(docs)

    # 3. Embed
    embeddings = get_embeddings_model()

    # 4. Store
    vectorstore = create_vector_store(splits, embeddings)

    # 5. Retrieve
    retriever = get_retriever(vectorstore)

    # 6. Generate
    rag_chain = create_rag_chain(retriever)

    # 7. Run
    response = rag_chain.invoke("What does RAG stand for?")
    print(f"Response: {response}")

if __name__ == "__main__":
    # Note: Requires OPENAI_API_KEY to run
    try:
        main()
    except Exception as e:
        print(f"Execution failed (likely missing API key or dependencies): {e}")
```

