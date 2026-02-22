import requests
import json

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

class GitHubRequest(BaseModel):
    github_url: str
app = FastAPI()

def fetch_and_summarize(url):

    response = requests.get(url)
    if response.status_code != 200:
        raise ConnectionError("Failed to fetch repository contents")
    try:
        contents = json.loads(response.content)
    except json.JSONDecodeError:
        return "Failed to parse repository contents as JSON"

    summary = f"Repository {url} has {len(contents)} files"
    return summary

@app.post("/summarize")
async def summarize(request: GitHubRequest):
    try:
        request_url = request.github_url
        summary = fetch_and_summarize(request_url)
        return {
            "summary": summary
        }

    except Exception as e:
        return {"status": "error",
                "message": str(e)}


@app.get("/hello")
async def say_hello():
    return {"message": f"Hello You there"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)