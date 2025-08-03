import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.request_model import ChatRequest

app = FastAPI()

@app.post("/chat")
def chat(request: ChatRequest):
    return {"response": f"Received message: {request.message}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
