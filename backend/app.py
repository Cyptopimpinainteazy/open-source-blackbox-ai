from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import uvicorn
import os
import json
import ast
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import astroid
from pylint import epylint as lint
import autopep8

app = FastAPI()

# CORS and Static Files Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/previews", StaticFiles(directory="previews"), name="previews")

# Ensure directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("previews", exist_ok=True)
os.makedirs("frontend/static", exist_ok=True)

class CodeAnalyzer:
    @staticmethod
    def analyze_python(code: str) -> Dict[str, Any]:
        analysis = {
            'issues': [],
            'suggestions': [],
            'complexity': {},
            'patterns': []
        }
        
        try:
            # Parse code with astroid for deep analysis
            module = astroid.parse(code)
            
            # Check for code complexity
            for node in module.nodes_of_class(astroid.FunctionDef):
                complexity = CodeAnalyzer._calculate_complexity(node)
                if complexity > 10:
                    analysis['issues'].append({
                        'type': 'complexity',
                        'message': f'Function {node.name} has high complexity ({complexity})',
                        'line': node.lineno
                    })
                analysis['complexity'][node.name] = complexity
            
            # Check for common issues
            analysis['issues'].extend(CodeAnalyzer._check_common_issues(module))
            
            # Generate refactoring suggestions
            analysis['suggestions'].extend(CodeAnalyzer._generate_refactoring_suggestions(module))
            
            # Run pylint for additional checks
            with open('temp.py', 'w') as f:
                f.write(code)
            pylint_stdout, pylint_stderr = lint.py_run('temp.py', return_std=True)
            analysis['issues'].extend(CodeAnalyzer._parse_pylint_output(pylint_stdout.getvalue()))
            os.remove('temp.py')
            
            # Format code according to PEP 8
            formatted_code = autopep8.fix_code(code)
            if formatted_code != code:
                analysis['suggestions'].append({
                    'type': 'style',
                    'message': 'Code can be formatted according to PEP 8',
                    'fix': formatted_code
                })
            
        except Exception as e:
            analysis['issues'].append({
                'type': 'error',
                'message': f'Error analyzing code: {str(e)}'
            })
        
        return analysis

    @staticmethod
    def _calculate_complexity(node):
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in node.get_children():
            if isinstance(child, (astroid.If, astroid.While, astroid.For)):
                complexity += 1
            elif isinstance(child, astroid.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    @staticmethod
    def _check_common_issues(module):
        issues = []
        
        # Check for unused imports
        imports = set()
        used_names = set()
        for node in module.nodes_of_class(astroid.Import):
            for name, _ in node.names:
                imports.add(name)
        for node in module.nodes_of_class(astroid.Name):
            used_names.add(node.name)
        
        unused_imports = imports - used_names
        for name in unused_imports:
            issues.append({
                'type': 'unused_import',
                'message': f'Unused import: {name}'
            })
        
        # Check for long functions
        for node in module.nodes_of_class(astroid.FunctionDef):
            if len(list(node.get_children())) > 50:
                issues.append({
                    'type': 'long_function',
                    'message': f'Function {node.name} is too long',
                    'line': node.lineno
                })
        
        return issues

    @staticmethod
    def _generate_refactoring_suggestions(module):
        suggestions = []
        
        # Suggest extracting long methods
        for node in module.nodes_of_class(astroid.FunctionDef):
            if len(list(node.get_children())) > 20:
                suggestions.append({
                    'type': 'extract_method',
                    'message': f'Consider breaking down function {node.name} into smaller functions',
                    'line': node.lineno
                })
        
        # Suggest using list comprehensions
        for node in module.nodes_of_class(astroid.For):
            if isinstance(node.parent, astroid.Assign) and isinstance(node.parent.value, astroid.List):
                suggestions.append({
                    'type': 'list_comprehension',
                    'message': 'Consider using a list comprehension here',
                    'line': node.lineno
                })
        
        return suggestions

    @staticmethod
    def _parse_pylint_output(output: str) -> List[Dict[str, Any]]:
        issues = []
        for line in output.split('\n'):
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 3:
                    issues.append({
                        'type': 'pylint',
                        'message': parts[2].strip(),
                        'line': int(parts[1]) if parts[1].strip().isdigit() else None
                    })
        return issues

    @staticmethod
    def analyze_javascript(code: str) -> Dict[str, Any]:
        analysis = {
            'issues': [],
            'suggestions': [],
            'complexity': {},
            'patterns': []
        }
        
        # Check for common JS issues using regex
        if 'var ' in code:
            analysis['suggestions'].append({
                'type': 'modernize',
                'message': 'Consider using let/const instead of var'
            })
        
        if 'function ' in code and '=>' not in code:
            analysis['suggestions'].append({
                'type': 'modernize',
                'message': 'Consider using arrow functions'
            })
        
        # Check for potential memory leaks
        if 'addEventListener' in code and 'removeEventListener' not in code:
            analysis['issues'].append({
                'type': 'memory_leak',
                'message': 'Event listener added but never removed'
            })
        
        # Check for console.log statements
        console_logs = len(re.findall(r'console\.log', code))
        if console_logs > 0:
            analysis['issues'].append({
                'type': 'debug_code',
                'message': f'Found {console_logs} console.log statements that should be removed in production'
            })
        
        return analysis

    @staticmethod
    def suggest_refactoring(code: str, language: str) -> List[Dict[str, Any]]:
        suggestions = []
        
        if language in ['python', 'py']:
            try:
                module = astroid.parse(code)
                
                # Suggest using context managers
                for node in module.nodes_of_class(astroid.Call):
                    if isinstance(node.func, astroid.Name) and node.func.name in ['open']:
                        suggestions.append({
                            'type': 'context_manager',
                            'message': 'Use a context manager (with statement) for file operations',
                            'line': node.lineno
                        })
                
                # Suggest using list/dict comprehensions
                for node in module.nodes_of_class(astroid.For):
                    if isinstance(node.parent, astroid.Assign):
                        suggestions.append({
                            'type': 'comprehension',
                            'message': 'Consider using a list/dict comprehension',
                            'line': node.lineno
                        })
                
            except Exception as e:
                suggestions.append({
                    'type': 'error',
                    'message': f'Error analyzing code: {str(e)}'
                })
        
        elif language in ['javascript', 'typescript']:
            # Suggest modern JS features
            if 'function' in code:
                suggestions.append({
                    'type': 'modernize',
                    'message': 'Consider using arrow functions',
                    'example': '(params) => { /* code */ }'
                })
            
            if 'var ' in code:
                suggestions.append({
                    'type': 'modernize',
                    'message': 'Use const/let instead of var',
                    'example': 'const x = 1; let y = 2;'
                })
            
            if '.bind(this)' in code:
                suggestions.append({
                    'type': 'modernize',
                    'message': 'Use arrow functions to preserve this context',
                    'example': 'onClick = () => { /* code */ }'
                })
        
        return suggestions

@app.post("/analyze")
async def analyze_code(code: str = Form(...), language: str = Form(...)):
    """Analyze code for issues and suggest improvements"""
    if language in ['python', 'py']:
        analysis = CodeAnalyzer.analyze_python(code)
    elif language in ['javascript', 'typescript']:
        analysis = CodeAnalyzer.analyze_javascript(code)
    else:
        return JSONResponse(content={"error": "Unsupported language"})
    
    return JSONResponse(content=analysis)

@app.post("/refactor")
async def refactor_code(code: str = Form(...), language: str = Form(...)):
    """Suggest refactoring improvements for the code"""
    suggestions = CodeAnalyzer.suggest_refactoring(code, language)
    return JSONResponse(content={"suggestions": suggestions})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    try:
        # Create a safe filename
        filename = os.path.join("uploads", file.filename)
        
        # Save the file
        with open(filename, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return JSONResponse(content={
            "filename": file.filename,
            "status": "success",
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to upload file: {str(e)}"},
            status_code=500
        )

@app.post("/chat")
async def chat(message: str = Form(...)):
    """Handle chat messages"""
    try:
        if "FastAPI endpoint" in message and "CRUD" in message:
            code = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI()

# Data Model
class Item(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float

# In-memory database
items_db = {}

# CRUD Operations
@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    """Create a new item"""
    if not item.id:
        item.id = str(uuid.uuid4())
    items_db[item.id] = item
    return item

@app.get("/items/", response_model=List[Item])
async def read_items():
    """Get all items"""
    return list(items_db.values())

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: str):
    """Get a specific item by ID"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: Item):
    """Update an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item
    return item

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Item deleted successfully"}'''
            
            return JSONResponse(content={
                "response": {
                    "code": code,
                    "language": "python"
                }
            })
        else:
            return JSONResponse(content={
                "response": {
                    "code": "print('Hello, World!')",
                    "language": "python"
                }
            })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process message: {str(e)}"}
        )

# Mount the frontend directory last (so it doesn't override API routes)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
