import os
from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Initialize components
def initialize_pipeline(csv_path):
    # Load CSV data
    loader = CSVLoader(file_path=csv_path)
    data = loader.load()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(data)
    
    # Create embeddings and vector store
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    # Initialize LLM
    llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
    
    return vectorstore, llm

# Create conversation chain
def create_conversation_chain(vectorstore, llm):
    # Retriever with increased k value to get more documents
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 20,  # Increased from 5 to 20 to get more documents
            "filter": None  # Remove any filtering to get all post types
        }
    )
    
    # Prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Instagram analytics expert. Analyze the provided engagement data and provide insights in a clear, concise format.

        If the user greets you, respond with a friendly greeting and ask how you can help with their Instagram analytics.

        For analysis requests:
        1. Calculate and compare average engagement metrics (likes, comments, shares, views) for each post type
        2. Present data in a simple summary table showing averages
        3. Highlight key insights with specific percentage differences (e.g., "Videos generate 25% more likes than images")
        4. Provide 2-3 specific, actionable recommendations based on the data

        Format your response as follows:
        - For greetings: Keep it simple and friendly
        - For analysis:
          * Summary Table (showing averages for each metric)
          * Key Insights (focus on percentage differences)
          * Recommendations (2-3 specific actions)

        Example format for comparison:
        | Post Type | Avg Likes | Avg Comments | Avg Shares | Avg Views |
        |-----------|-----------|--------------|------------|-----------|
        | Images    | 2,500     | 1,200       | 800        | 3,000     |
        | Videos    | 3,125     | 1,500       | 1,000      | 3,750     |

        Key Insights:
        - Videos generate 25% more likes than images
        - Videos have 20% higher comment engagement
        - Video views are 25% higher than image views

        When analyzing the data:
        1. Calculate averages for each metric by post type
        2. Compare the averages to find percentage differences
        3. Focus on the most significant differences
        4. Provide recommendations based on the data

        Use the following context for your analysis:
        {context}
        
        Current conversation:
        {history}
        
        Question: {input}"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    # Chain
    chain = (
        {
            "context": lambda x: retriever.invoke(x["input"] if isinstance(x, dict) else x),
            "input": lambda x: x["input"] if isinstance(x, dict) else x,
            "history": lambda x: x.get("history", []) if isinstance(x, dict) else []
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Add conversation history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: ChatMessageHistory(),
        input_messages_key="input",
        history_messages_key="history",
    )
    
    return chain_with_history

# Main function
def main():
    # Path to your Instagram analytics CSV
    csv_path = r"C:\Users\veera\Downloads\Social_Media_Engagement_Analytics\backend\generated_data.csv"  # Replace with your file path
    
    # Initialize pipeline
    vectorstore, llm = initialize_pipeline(csv_path)
    conversation_chain = create_conversation_chain(vectorstore, llm)
    
    print("Instagram Analytics Assistant initialized. Type 'exit' to quit.")
    
    # Conversation loop
    while True:
        query = input("\nYour question: ")
        if query.lower() == 'exit':
            break
            
        # Invoke the chain
        response = conversation_chain.invoke(
            {"input": query},
            config={"configurable": {"session_id": "abc123"}},
        )
        
        print("\nAssistant:")
        print(response)

if __name__ == "__main__":
    main()