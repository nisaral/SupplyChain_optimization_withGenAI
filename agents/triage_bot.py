import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
import argparse

# Setup DB connection string
# Format: postgresql+psycopg2://user:password@host:port/dbname
DB_URI = "postgresql+psycopg2://admin:adminpassword@localhost:5433/supply_chain"

def get_sql_agent():
    # Make sure OPENAI_API_KEY is set in your environment variables
    if "OPENAI_API_KEY" not in os.environ:
        print("Warning: OPENAI_API_KEY not found in environment variables. Please set it before running queries.")

    db = SQLDatabase.from_uri(DB_URI)
    
    # Initialize the LLM
    # We use GPT-4 or GPT-3.5-turbo (adjust based on availability/cost)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # Create the SQL Agent
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=None,  # We can also use SQLDatabaseToolkit
        db=db,
        agent_type="openai-tools",
        verbose=True
    )
    return agent_executor

def interactive_chat():
    print("Initializing Supply Chain Smart Triage Bot (SQL Agent)...")
    try:
        agent = get_sql_agent()
        print("\nBot is ready! Type 'exit' to quit.")
        print("Example questions:")
        print("- How many exceptions did we have today?")
        print("- What is the total order value shipped by Air?")
        print("- Which truck route is currently delayed? (if tracking events exist)")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            try:
                response = agent.invoke({"input": user_input})
                print(f"\nBot: {response['output']}")
            except Exception as e:
                print(f"\nError querying agent: {e}")
                
    except Exception as e:
        print(f"Failed to initialize agent. Is the database running? Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supply Chain GenAI Smart Triage Bot")
    parser.add_argument("--query", type=str, help="Single query to ask the bot")
    args = parser.parse_args()

    if args.query:
        agent = get_sql_agent()
        response = agent.invoke({"input": args.query})
        print(f"\nBot: {response['output']}")
    else:
        interactive_chat()
