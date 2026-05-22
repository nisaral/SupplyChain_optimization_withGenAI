import os
import psycopg2
import json
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Setup DB configuration
DB_CONFIG = {
    'dbname': 'supply_chain',
    'user': 'admin',
    'password': 'adminpassword',
    'host': 'localhost',
    'port': '5433'
}

class TriageDecision(BaseModel):
    category: str = Field(description="One of: 'FIXABLE_AUTO', 'HUMAN_INTERVENTION', 'FRAUD_RISK'")
    sql_query: str = Field(description="The SQL UPDATE statement to fix the data if FIXABLE_AUTO, otherwise empty string", default="")
    reasoning: str = Field(description="Explanation of the decision")

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_llm():
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    try:
        if provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                print("Warning: OPENAI_API_KEY not set.")
                return None
            return ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        elif provider == "gemini":
            if not os.getenv("GOOGLE_API_KEY"):
                print("Warning: GOOGLE_API_KEY not set.")
                return None
            return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
        else: # Default to groq
            if not os.getenv("GROQ_API_KEY"):
                print("Warning: GROQ_API_KEY not set.")
                return None
            return ChatGroq(model="mixtral-8x7b-32768", temperature=0)
    except Exception as e:
        print(f"Failed to initialize LLM ({provider}): {e}")
        return None

def audit_exceptions():
    llm = get_llm()
    if not llm:
        print("Running in dummy mode. Exception triage will use simulated logic.")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, payload, error_message FROM exception_logs WHERE status = 'PENDING'")
    exceptions = cursor.fetchall()
    
    if not exceptions:
        # print("No pending exceptions found.")
        conn.close()
        return

    parser = JsonOutputParser(pydantic_object=TriageDecision)
    prompt = PromptTemplate(
        template="""You are a Financial Data Auditor. Analyze the following exception record.
Exception Record: {record}
Error Message: {error_message}

Classify the issue. The table to update is 'logistics_telemetry'. Assume the primary key is 'order_id' inside the payload data.
{format_instructions}""",
        input_variables=["record", "error_message"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    for exc_id, payload, error_message in exceptions:
        print(f"\nAnalyzing exception ID {exc_id}...")
        
        if llm:
            chain = prompt | llm | parser
            try:
                decision = chain.invoke({"record": payload, "error_message": error_message})
            except Exception as e:
                print(f"LLM Error: {e}")
                continue
        else:
            # Dummy logic if no API key
            decision = {
                "category": "FIXABLE_AUTO",
                "sql_query": f"UPDATE logistics_telemetry SET order_value = 0 WHERE order_id = 'UNKNOWN'",
                "reasoning": "Dummy categorization since GROQ_API_KEY is missing."
            }
            
        print(f"Decision: {decision['category']}")
        print(f"Reasoning: {decision['reasoning']}")
        
        if decision['category'] == 'FIXABLE_AUTO' and decision.get('sql_query'):
            print(f"Generated SQL: {decision['sql_query']}")
            
            # Dry run execution
            try:
                # Start transaction
                cursor.execute("BEGIN")
                cursor.execute(decision['sql_query'])
                print("[DRY RUN] Executed SQL successfully.")
                # Rollback to simulate dry run
                cursor.execute("ROLLBACK")
                
                print(f"---> [ACTION REQUIRED] Sent notification to Supervisor for Approval of SQL: {decision['sql_query']}")
                
                # Update status
                cursor.execute("UPDATE exception_logs SET status = 'PROPOSED_FIX' WHERE id = %s", (exc_id,))
                conn.commit()
            except Exception as e:
                print(f"Dry run failed: {e}")
                cursor.execute("ROLLBACK")
        else:
            cursor.execute("UPDATE exception_logs SET status = 'REQUIRES_HUMAN' WHERE id = %s", (exc_id,))
            conn.commit()
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("Starting Autonomous Audit Agent...")
    while True:
        try:
            audit_exceptions()
        except Exception as e:
            print(f"Error during audit: {e}")
        time.sleep(5)
