# FastAPI Basics

## What is FastAPI?
FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints. It is one of the fastest Python frameworks available, on par with NodeJS and Go.

## Creating your first endpoint
To create a GET endpoint in FastAPI, use the @app.get() decorator.

from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

## Path Parameters
You can declare path parameters with the same syntax used by Python format strings.

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

## Query Parameters
When you declare function parameters that are not part of the path, they become query parameters.

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

## POST Endpoints with Request Body
Use Pydantic models to declare a request body.

from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
def create_item(item: Item):
    return item

## HTTP Status Codes
FastAPI handles status codes automatically.
200 means Success.
201 means Created.
404 means Not Found.
422 means Validation Error.
500 means Internal Server Error.

## Running FastAPI
Start the server with this command.
uvicorn main:app --reload --port 8000
The reload flag makes the server restart automatically when you change code.

## Interactive API Docs
FastAPI automatically generates documentation at these locations.
http://localhost:8000/docs for Swagger UI.
http://localhost:8000/redoc for ReDoc.

## Dependency Injection
FastAPI has a powerful dependency injection system using the Depends function.

from fastapi import Depends

def get_db():
    db = connect_to_database()
    return db

@app.get("/users/")
def get_users(db=Depends(get_db)):
    return db.query_all_users()

## Error Handling
Use HTTPException to return error responses.

from fastapi import HTTPException

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

## Request Validation
FastAPI automatically validates request data using Pydantic.
If validation fails, it returns a 422 error with details about what went wrong.

## Response Models
You can specify the response model using the response_model parameter.

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    return item

## CORS Middleware
To allow requests from a browser frontend, add CORS middleware.

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

## Background Tasks
FastAPI supports background tasks that run after returning a response.

from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(message)

@app.post("/send/")
def send_notification(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "notification sent")
    return {"message": "Notification sent"}