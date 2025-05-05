# Open Source Blackbox.ai

This project is an open source version of blackbox.ai running locally, inspired by GPT4All. It supports chat interaction with a local AI model and training from local files.

## Features

- Chat interface with a local AI model (placeholder echo response currently)
- Upload local files for training the AI model
- Simple frontend UI using Tailwind CSS
- Backend API using FastAPI

## Prerequisites

- Python 3.8+
- pip

## Setup

1. Clone the repository (if applicable) or download the project files.

2. Install Python dependencies:

```bash
pip install fastapi uvicorn python-multipart transformers torch
```

3. Download and set up the Code LLaMA and StarCoder models:

- Download the Code LLaMA model weights from the official source or Hugging Face.
- Extract and place the model files in a directory, e.g., `path/to/codellama-model`.
- Download the StarCoder model weights from the official source or Hugging Face.
- Extract and place the model files in a directory, e.g., `path/to/starcoder-model`.
- Update the `codellama_model_name` and `starcoder_model_name` variables in `backend/app.py` with the paths to the respective model directories.

4. Run the backend server:

```bash
python backend/app.py
```

The backend will start on `http://localhost:8000`.

5. Open the frontend:

Open the `frontend/index.html` file in your browser directly or serve it using a simple HTTP server:

```bash
# Using Python 3
python -m http.server 8080 -d frontend
```

Then open `http://localhost:8080` in your browser.

## Usage

- Use the chat input to send messages to the AI model.
- Upload files using the file upload section to add local files for training.
- The backend chat endpoint uses Code LLaMA and StarCoder models for code generation and chat responses.
- Specialized support for cryptocurrency bot code generation is included.

## Next Steps

- Implement training pipeline to fine-tune the models with uploaded files.
- Improve frontend UI and UX.
- Expand cryptocurrency bot code generation capabilities with more examples and datasets.

## License

This project is open source and free to use.
