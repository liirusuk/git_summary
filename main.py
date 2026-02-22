import requests
import json

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

class GitHubRequest(BaseModel):
    github_url: str
app = FastAPI()

def load_first_look_prompt():
    with open("llm_first_look.txt", "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def load_summary_prompt():
    with open("llm_json_summary.txt", "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def fetch_repo_file_tree(github_url: str) -> list[str]:

    repo_path = github_url.rstrip("/").split("github.com/")[-1]
    raw_base = f"https://raw.githubusercontent.com/{repo_path}/main"
    base_url = f"https://api.github.com/repos/{repo_path}/git"
    api_url = f"{base_url}/trees/main?recursive=1"

    response = requests.get(api_url)
    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch repository tree (status {response.status_code})")

    tree_data = response.json()
    if "tree" not in tree_data:
        raise ValueError("Unexpected response format from GitHub API")
    return raw_base, [item["path"] for item in tree_data["tree"] if item["type"] == "blob"]


def get_main_file_list(file_paths: list) -> list:
    user_message = "File tree:\n" + "\n".join(file_paths)

    client = OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY")
    )
    SYSTEM_PROMPT = load_first_look_prompt()
    completion = client.chat.completions.create(
        model="Qwen/Qwen3-Coder-30B-A3B-Instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.0,
    )
    return completion.choices[0].message.content.strip().split("\n")

def read_files_content(files: list[str]) -> list[str]:
    files_content = {}
    for f in files:
        try:
            response = requests.get(f)
            if response.status_code != 200:
                raise ConnectionError(f"Failed to fetch repository tree (status {response.status_code})")
            data = response.content.decode("utf-8", errors="replace")
            files_content[f] = data
        except Exception as e:
            files_content[f] = 'Error: {}'.format(str(e))
    return files_content

def get_summary(file_paths: list, files_content: dict[str, str]) -> list:
    user_message = "File tree:\n" + "\n".join(file_paths)
    user_message += "\n" + "Files content:\n" + "\n".join([':'.join([x, y]) for x,y in files_content.items()])

    client = OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY")
    )
    SYSTEM_PROMPT = load_summary_prompt()
    completion = client.chat.completions.create(
        model="Qwen/Qwen3-Coder-30B-A3B-Instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.0,
    )
    return json.loads(completion.choices[0].message.content)

def fetch_and_summarize(github_url):
    try:
        raw_base, file_paths = fetch_repo_file_tree(github_url)
        files = get_main_file_list(file_paths)
        files_content = read_files_content([f'{raw_base}/{f}' for f in files if '`' not in f])
        summary = get_summary(file_paths, files_content)
    except json.JSONDecodeError:
        return "Failed to parse repository contents as JSON"

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