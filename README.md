# Repository Summary Service
A tiny FastAPI service that, given a public GitHub repository URL, returns a concise JSON summary of the project.
## 📦 Chosen Model
**Qwen/Qwen3‑Coder‑30B‑A3B‑Instruct** – a powerful instruction‑tuned LLM that works well for code‑centric tasks.
## 🚀 Setup & Run (Fresh Machine)
Prerequisite: Python 3.14+ installed and added to your PATH.
1. **Clone the repository**

``` bash
   git clone <repository‑url>
   cd <repository‑directory>
```

2. **Create a virtual environment**

``` bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
```

3. **Install dependencies**

``` bash
   pip install --upgrade pip
   pip install -r requirements.txt
```

The requirements.txt contains:

``` 
   fastapi
   uvicorn
   requests
   pydantic
   openai
```

4. **Set the API key**
The service talks to the Nebius LLM endpoint; you need an API key.
``` bash
   set NEBIUS_API_KEY=YOUR_KEY            # Windows
   export NEBIUS_API_KEY=YOUR_KEY         # macOS / Linux
```

5. **Start the server**

``` bash
   python main.py
   # or, equivalently
   uvicorn main:app --host 0.0.0.0 --port 8000
```

6. **Use the API**
 - Hello endpoint (sanity check)
``` 
     GET http://localhost:8000/hello
```

 - Summarize a GitHub repo

``` bash
     curl -X POST http://localhost:8000/summarize \
          -H "Content-Type: application/json" \
          -d '{"github_url": "https://github.com/owner/repo"}'
```

The response will be a JSON object with three fields:

``` json
   {
     "summary": "...",
     "technologies": ["Python", "FastAPI", "uvicorn", "..."],
     "structure": "..."
   }
```

 
## 📂 How Repository Contents Are Handled

1. **Tree Retrieval** – The service calls the GitHub API (`/git/trees/main?recursive=1`) to obtain a flat list of every file (blob) in the default branch.
2. **File Selection** –
 - The complete file‑list is sent to the first‑look LLM prompt.
 - The model returns a short list of representative file paths (entry points, core modules, configuration files, etc.).
 - This step keeps the downstream processing lightweight by focusing only on the most informative files.
3. **Content Fetching** – For each selected path, the raw file is downloaded from the `raw.githubusercontent.com` endpoint.
4. **Summarization** –
 - The file‑tree and the fetched file contents are fed to a second LLM prompt (JSON‑summary).
 - The model produces a structured JSON summary (project purpose, technologies, layout).
5. *What’s Skipped & Why*
 - Non‑code assets (images, binaries, large data files) – they rarely help a textual summary and would waste bandwidth.
 - Files containing back‑ticks (`) in their path – the implementation explicitly filters these out, assuming they are markup‑related or temporary artifacts.
 - Huge files – the LLM prompt size limit forces us to ignore files whose content would push the request beyond the token budget.

 
The result is a fast, low‑overhead service that gives you a clear, human‑readable overview of any public Python‑based repository.