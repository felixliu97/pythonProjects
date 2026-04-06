# Langchain Cheatsheet

=============================
A comprehensive reference for building LLM applications using LangChain (v0.1 / v0.2+).
Focuses on the modern LCEL (LangChain Expression Language) syntax.

PREREQUISITES:
--------------
1.  **Installation**: `pip install langchain langchain-openai langchain-community langchain-core`
    -   Optional: `langchain-anthropic`, `chromadb`, etc.
2.  **API Keys**: Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc., in your environment.

SECTIONS:
---------
1. Models (IO) - ChatModels vs LLMs
2. Prompts - Templates & Messages
3. Output Parsers - Structured Data
4. LCEL - Chains & Runnables
5. RAG - Retrieval Augmented Generation
6. Memory - Chat History
7. Agents - Tools & Reasoning

``` python
import os
# from dotenv import load_dotenv
# load_dotenv() # Load env vars from .env
```

## 1. MODELS (ChatModels vs LLMs)

``` python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def chat_models():
    """
        They accept a list of Messages and return an AIMessage.

    """
    # Initialize
    chat = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # 1. Basic Invocation
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Explain recursion in one sentence.")
    ]
    response = chat.invoke(messages)
    print(f"Response: {response.content}")
    
    # 2. Streaming (Token by Token)
    print("Streaming: ", end="")
    for chunk in chat.stream("Tell me a quick joke."):
        print(chunk.content, end="", flush=True)
    print()
```

## 2. PROMPTS

``` python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def prompt_templates():
    """
    """
    # 1. Simple Template from string
    template = ChatPromptTemplate.from_template("Tell me a joke about {topic}.")
    formatted = template.invoke({"topic": "cats"})
    # Result is a list of messages: [HumanMessage(content='Tell me a joke about cats.')]
    
    # 2. Complex Chat Template (System + User)
    chat_template = ChatPromptTemplate.from_messages([
        ("system", "You are a pirate captain. Answer everything with a 'Yarr'."),
        ("user", "{input}")
    ])
    
    return chat_template
```

## 3. OUTPUT PARSERS

``` python
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# Pydantic schema for structured output
class Joke(BaseModel):
    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline of the joke")

def output_parsers():
    """
    """
    # 1. String Parser (Just gets the .content)
    str_parser = StrOutputParser()
    
    # 2. JSON/Pydantic Parser
    json_parser = JsonOutputParser(pydantic_object=Joke)
    
    return str_parser, json_parser
```

## 4. LCEL (CHAINS)

``` python
def lcel_chains():
    """
        Pattern: Input -> Prompt -> Model -> OutputParser

    """
    model = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = ChatPromptTemplate.from_template("Explain {topic} simply.")
    parser = StrOutputParser()
    
    # Create the chain
    chain = prompt | model | parser
    
    # Invoke
    result = chain.invoke({"topic": "quantum entanglement"})
    print(f"Chain Result: {result}")
    
    return chain
```

## 5. RAG (RETRIEVAL)

``` python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def rag_pipeline():
    """
    """
    # 1. Load
    # loader = TextLoader("./my_data.txt")
    # docs = loader.load()
    
    # 2. Split
    # splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # splits = splitter.split_documents(docs)
    
    # 3. Embed & Store (VectorStore)
    # vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    
    # 4. Retrieve
    # retriever = vectorstore.as_retriever()
    
    # 5. RAG Chain
    # rag_chain = (
    #     {"context": retriever, "question": RunnablePassthrough()} 
    #     | prompt 
    #     | model 
    #     | parser
    # )
    pass
```

## 6. MEMORY (CHAT HISTORY)

``` python
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

store = {} # Dictionary to store histories by session_id

def get_session_history(session_id: str):
    """
    Function get_session_history
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def memory_chain():
    """
    Function memory_chain
    """
    model = ChatOpenAI()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="history"), # History injected here
        ("human", "{input}"),
    ])
    
    chain = prompt | model | StrOutputParser()
    
    # Wrap chain with history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    
    # Invoke with session_id
    config = {"configurable": {"session_id": "user_1"}}
    response1 = chain_with_history.invoke({"input": "Hi, I'm Bob."}, config=config)
    response2 = chain_with_history.invoke({"input": "What's my name?"}, config=config)
    print(f"Memory Response: {response2}") # Should say "Bob"
```

## 7. AGENTS

``` python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool

@tool
def diff(a: int, b: int) -> int:
    """
    Calculates the difference between two numbers.

    """
    return a - b

def simple_agent():
    """
    Function simple_agent
    """
    model = ChatOpenAI(temperature=0)
    tools = [diff]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Use tools if needed."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # Construct Agent
    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # Run
    agent_executor.invoke({"input": "What is 100 minus 35?"})
```

## MAIN

``` python
if __name__ == "__main__":
    print("--- LangChain Cheatsheet Examples ---")
    # chat_models()
    # lcel_chains()
    # memory_chain()
    # simple_agent()
    print("Uncomment functions in main() to run examples.")
```

