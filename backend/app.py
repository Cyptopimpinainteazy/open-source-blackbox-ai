from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import uvicorn
import os
import json
from datetime import datetime

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("previews", exist_ok=True)

# Serve static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/previews", StaticFiles(directory="previews"), name="previews")

# Database setup
def init_db():
    conn = sqlite3.connect('code_assistant.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS code_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            code TEXT,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preview_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Code Templates
CODE_TEMPLATES = {
    "html": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-4">Hello World</h1>
        <p class="text-gray-600">This is a generated page.</p>
    </div>
</body>
</html>
""",
    "react": """
import React, { useState, useEffect } from 'react';

interface Props {
  title: string;
}

const App: React.FC<Props> = ({ title }) => {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch('/api/data');
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">{title}</h1>
      <div className="grid gap-4">
        {data.map((item) => (
          <div key={item.id} className="p-4 bg-white rounded shadow">
            {item.name}
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
""",
    "api": """
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: str

items: List[Item] = []

@app.get("/items")
async def get_items():
    return items

@app.post("/items")
async def create_item(item: Item):
    item.id = len(items) + 1
    items.append(item)
    return item

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = next((item for item in items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
"""
}

def create_preview(code: str, language: str) -> str:
    """Create a preview file for the code if it's previewable"""
    if language in ['html', 'javascript', 'typescript']:
        preview_path = f"previews/preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        if language == 'html':
            content = code
        else:
            content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/javascript">
        {code}
    </script>
</body>
</html>
"""
        with open(preview_path, 'w') as f:
            f.write(content)
        return preview_path
    return None

def save_to_db(title: str, description: str, code: str, language: str, preview_path: str = None):
    conn = sqlite3.connect('code_assistant.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO code_snippets (title, description, code, language, preview_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, code, language, preview_path))
    conn.commit()
    conn.close()

def get_recent_snippets(limit: int = 5):
    conn = sqlite3.connect('code_assistant.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, description, code, language, preview_path
        FROM code_snippets
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    snippets = c.fetchall()
    conn.close()
    return [
        {
            'id': s[0],
            'title': s[1],
            'description': s[2],
            'code': s[3],
            'language': s[4],
            'preview_path': s[5]
        }
        for s in snippets
    ]

def detect_language(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(kw in prompt_lower for kw in ["html", "webpage", "website"]):
        return "html"
    elif any(kw in prompt_lower for kw in ["react", "component", "ui"]):
        return "typescript"
    return "python"

def generate_code(prompt: str) -> tuple[str, str]:
    language = detect_language(prompt)
    
    if language == "html":
        return language, CODE_TEMPLATES["html"]
    elif language == "typescript":
        return language, CODE_TEMPLATES["react"]
    else:
        return "python", CODE_TEMPLATES["api"]

@app.post("/chat")
async def chat(message: str = Form(...)):
    # Generate code
    language, code = generate_code(message)
    
    # Create preview if possible
    preview_path = create_preview(code, language)
    
    # Save to database
    save_to_db(
        title=message[:50],
        description=message,
        code=code,
        language=language,
        preview_path=preview_path
    )
    
    # Prepare response
    response = {
        'code': code,
        'language': language,
        'preview_path': preview_path
    }
    
    return JSONResponse(content={"response": json.dumps(response)})

@app.get("/recent")
async def get_recent():
    return JSONResponse(content={"snippets": get_recent_snippets()})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create preview for uploaded file if it's previewable
    extension = file.filename.split('.')[-1].lower()
    if extension in ['html', 'js', 'ts']:
        content_str = content.decode('utf-8')
        preview_path = create_preview(content_str, extension)
        return {
            "filename": file.filename,
            "preview_path": preview_path,
            "message": "File uploaded successfully"
        }
    
    return {"filename": file.filename, "message": "File uploaded successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
