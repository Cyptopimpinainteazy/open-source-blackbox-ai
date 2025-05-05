from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import for Code LLaMA and StarCoder integration (placeholder)
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None

app = FastAPI()

# Allow CORS for frontend running on different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Code LLaMA and StarCoder models and tokenizers (placeholder)
codellama_model = None
codellama_tokenizer = None
starcoder_model = None
starcoder_tokenizer = None

if AutoModelForCausalLM and AutoTokenizer and torch:
    try:
        codellama_model_name = "path/to/codellama-model"  # Update with actual model path
        codellama_tokenizer = AutoTokenizer.from_pretrained(codellama_model_name)
        codellama_model = AutoModelForCausalLM.from_pretrained(codellama_model_name)
        codellama_model.eval()
    except Exception as e:
        print(f"Error loading Code LLaMA model: {e}")

    try:
        starcoder_model_name = "path/to/starcoder-model"  # Update with actual model path
        starcoder_tokenizer = AutoTokenizer.from_pretrained(starcoder_model_name)
        starcoder_model = AutoModelForCausalLM.from_pretrained(starcoder_model_name)
        starcoder_model.eval()
    except Exception as e:
        print(f"Error loading StarCoder model: {e}")

def generate_code_with_codellama(prompt: str) -> str:
    if not codellama_model or not codellama_tokenizer:
        return "Code LLaMA model not loaded. Please set up the model."
    inputs = codellama_tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = codellama_model.generate(**inputs, max_length=512)
    generated = codellama_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated

def generate_code_with_starcoder(prompt: str) -> str:
    if not starcoder_model or not starcoder_tokenizer:
        return "StarCoder model not loaded. Please set up the model."
    inputs = starcoder_tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = starcoder_model.generate(**inputs, max_length=512)
    generated = starcoder_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated

# Placeholder for chat endpoint
@app.post("/chat")
async def chat(message: str = Form(...)):
    # Specialized handling for cryptocurrency bot code generation
    if any(keyword in message.lower() for keyword in ["crypto bot", "cryptocurrency bot", "trading bot", "binance bot", "crypto trading"]):
        # Provide a sample crypto trading bot code snippet (placeholder)
        crypto_bot_code = """
import ccxt
import time

exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
})

symbol = 'BTC/USDT'
timeframe = '1m'

def fetch_latest_price():
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

def simple_moving_average(prices, period):
    return sum(prices[-period:]) / period

def main():
    prices = []
    while True:
        price = fetch_latest_price()
        prices.append(price)
        if len(prices) > 20:
            sma_short = simple_moving_average(prices, 5)
            sma_long = simple_moving_average(prices, 20)
            if sma_short > sma_long:
                print("Buy signal")
            elif sma_short < sma_long:
                print("Sell signal")
        time.sleep(60)

if __name__ == "__main__":
    main()
"""
        response = f"Here is a sample cryptocurrency trading bot code:\n```python\n{crypto_bot_code}\n```"
    elif "full app" in message.lower() or "complete app" in message.lower() or "full project" in message.lower():
        # Include a crypto bot example in the full project structure
        project = {
            "files": [
                {
                    "filename": "crypto_bot.py",
                    "content": crypto_bot_code
                },
                {
                    "filename": "README.md",
                    "content": "# Crypto Trading Bot\\nThis is a simple crypto trading bot using ccxt library."
                }
            ]
        }
        import json
        response = f"Here is a full crypto bot project structure:\n{json.dumps(project)}"
    elif "write code" in message.lower() or "generate code" in message.lower() or "code" in message.lower():
        # Use both models to generate code and combine results
        code1 = generate_code_with_codellama(message)
        code2 = generate_code_with_starcoder(message)
        combined_code = f"Code LLaMA output:\n{code1}\n\nStarCoder output:\n{code2}"
        response = f"Here is the generated code from both models:\n```python\n{combined_code}\n```"
    else:
        response = f"Echo: {message}"
    return JSONResponse(content={"response": response})

# Endpoint to upload files for training
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save the uploaded file locally for training
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "message": "File uploaded successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
