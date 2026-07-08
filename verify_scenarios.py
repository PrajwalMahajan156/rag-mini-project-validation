import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"

def test_upload(file_path):
    print(f"\n--- Testing Upload: {os.path.basename(file_path)} ---")
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return None
    files = {"file": open(file_path, "rb")}
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files)
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Document ID: {data['document_id']}")
            return data["document_id"]
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

def test_chat(query, document_id, session_id=None):
    print(f"\n--- Testing Chat: '{query}' ---")
    params = {
        "query": query,
        "document_id": document_id
    }
    if session_id:
        params["session_id"] = session_id
        
    try:
        response = requests.get(f"{BASE_URL}/chat", params=params, stream=True)
        if response.status_code == 200:
            print("Response: ", end="", flush=True)
            full_response = ""
            for chunk in response.iter_content(chunk_size=None):
                text = chunk.decode("utf-8")
                print(text, end="", flush=True)
                full_response += text
            print("\n")
            return full_response
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error during chat: {e}")
        return None

def run_all_tests():
    # 1. Test Multiple File Formats (using existing files in uploads if possible)
    # Based on list_dir output from Step 46
    test_files = [
        "/home/prajwal-mahajan/Desktop/RAG Delevarebal/MAIN_PROJECT_FOR_RAG/uploads/ce482d83-257c-41f2-890b-9e0e6f9e6a28.txt",
        "/home/prajwal-mahajan/Desktop/RAG Delevarebal/MAIN_PROJECT_FOR_RAG/uploads/8b40dd69-6bd7-4af3-a611-ee67a283328d.csv"
    ]
    
    # We'll use the .txt file for context QA tests
    txt_doc_id = test_upload(test_files[0])
    
    if txt_doc_id:
        # 2. Test Context-Aware QA
        print("\n--- Scenario: In-Context QA ---")
        test_chat("What is the main topic of this document?", txt_doc_id)
        
        print("\n--- Scenario: Out-of-Context QA ---")
        test_chat("What is the capital of France?", txt_doc_id)
        
        # 3. Test Multi-turn Conversation
        print("\n--- Scenario: Multi-turn Conversation ---")
        session_id = f"test_session_{int(time.time())}"
        test_chat("Summary this document in 2 sentences.", txt_doc_id, session_id)
        test_chat("Can you explain it in simpler terms?", txt_doc_id, session_id)

    # 4. Test Tabular Data
    csv_doc_id = test_upload(test_files[1])
    if csv_doc_id:
        print("\n--- Scenario: Tabular Data QA ---")
        test_chat("List all the names in this file.", csv_doc_id)

if __name__ == "__main__":
    run_all_tests()
