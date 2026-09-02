#!/usr/bin/env python3
"""
PMC CMS Chatbot Terminal CLI
Usage:
    python ask.py "पेंडिंग असणाऱ्या तक्रारींची एकूण संख्या किती आहे?"
    python ask.py "Show total complaints by status"
    python ask.py  (Interactive mode)
"""

import sys
import json
import requests

API_URL = "http://localhost:8000/api/vanna/v2/chat_sse"
HEADERS = {
    "Content-Type": "application/json",
    "Cookie": "vanna_email=admin@example.com"
}

def ask_question(question: str, conversation_id: str = "cli-session"):
    payload = {
        "message": question,
        "conversation_id": conversation_id
    }
    
    print(f"\n\033[1;36m❓ QUESTION:\033[0m {question}")
    print("\033[90m--------------------------------------------------\033[0m")
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True, timeout=60)
        sql_printed = set()
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                msg = json.loads(data_str)
                rich = msg.get("rich")
                if rich:
                    r_type = rich.get("type")
                    r_data = rich.get("data", {}) or {}
                    
                    # Print SQL query if executed
                    if r_type == "status_card" and r_data.get("metadata", {}).get("sql"):
                        sql = r_data["metadata"]["sql"]
                        if sql not in sql_printed:
                            print(f"\n\033[1;33m💻 SQL EXECUTED:\033[0m\n\033[32m{sql}\033[0m\n")
                            sql_printed.add(sql)
                            
                    # Print Text content
                    elif r_type == "text" and r_data.get("content"):
                        print(f"\033[1;35m🤖 RESPONSE:\033[0m\n{r_data['content']}\n")
                        
                simple = msg.get("simple")
                if simple and simple.get("text"):
                    stext = simple["text"].strip()
                    if stext and "Tool completed successfully" not in stext and "IMPORTANT:" not in stext:
                        print(stext)
            except Exception:
                pass
                
        print("\033[90m--------------------------------------------------\033[0m\n")
    except Exception as e:
        print(f"\033[1;31mError:\033[0m {e}")

def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        ask_question(question)
    else:
        print("\033[1;32m==================================================\033[0m")
        print("\033[1;32m      PMC CMS Chatbot Interactive CLI             \033[0m")
        print("\033[1;32m==================================================\033[0m")
        print("Type your question in Marathi or English (or 'exit' to quit):\n")
        
        count = 1
        while True:
            try:
                question = input("\033[1;34mYou > \033[0m").strip()
                if not question:
                    continue
                if question.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                ask_question(question, conversation_id=f"interactive-{count}")
                count += 1
            except (KeyboardInterrupt, EOFError):
                print("\nExiting CLI.")
                break

if __name__ == "__main__":
    main()
