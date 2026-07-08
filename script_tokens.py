import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import Config

# Set API Key manually if needed for this script
os.environ["GOOGLE_API_KEY"] = Config.GOOGLE_API_KEY

def test_stream_tokens():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=Config.GOOGLE_API_KEY,
        streaming=True
    )
    
    print("Streaming started...")
    total_chunks = 0
    usage_found = False
    
    final_chunk = None
    for chunk in llm.stream("Say 'Hello' then explain gravity in one sentence."):
        total_chunks += 1
        final_chunk = chunk
        print(f"Chunk {total_chunks}: {repr(chunk.content)}")
    
    print("\n--- Final Chunk Inspection ---")
    print(f"Attributes: {dir(final_chunk)}")
    if hasattr(final_chunk, 'usage_metadata'):
        print(f"usage_metadata: {final_chunk.usage_metadata}")
    if hasattr(final_chunk, 'response_metadata'):
        print(f"response_metadata: {final_chunk.response_metadata}")
    
    # Try using result from invoke to see if tokens appear there
    print("\n--- Testing Invoke (non-streaming) ---")
    res = llm.invoke("Say 'Hi'")
    print(f"Invoke result usage_metadata: {getattr(res, 'usage_metadata', 'Not Found')}")
    print(f"Invoke result response_metadata: {getattr(res, 'response_metadata', 'Not Found')}")
             
    if not usage_found:
        print("NO USAGE METADATA FOUND IN ANY CHUNK.")
    else:
        print("Usage metadata was found.")

if __name__ == "__main__":
    test_stream_tokens()
