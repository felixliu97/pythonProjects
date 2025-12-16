# FastAPI Cheatsheet

## FASTAPI CHEATSHEET

## 1. SETUP & BASICS

```python
# Installation
# pip install "fastapi[standard]"

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Run with CLI
# fastapi dev main.py
```

## 2. PARAMETERS

### Path Parameters

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### Query Parameters

```python
from fastapi import Query

# /items/?skip=0&limit=10
@app.get("/items/")
def read_items(
    skip: int = 0, 
    limit: int = 10, 
    q: str | None = Query(default=None, max_length=50)
):
    return {"skip": skip, "limit": limit, "q": q}
```

## 3. REQUEST BODY & PYDANTIC

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None

@app.post("/items/")
def create_item(item: Item):
    return item
```

## 4. RESPONSES & STATUS CODES

```python
from fastapi import HTTPException, status

class ItemOut(BaseModel):
    name: str
    price_with_tax: float

@app.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    if item.name == "Foo":
        raise HTTPException(status_code=400, detail="Item already exists")
    return item
```

## 5. DEPENDENCIES

```python
from fastapi import Depends

def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
def read_items(commons: dict = Depends(common_parameters)):
    return commons

# Database Dependency Pattern
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    ...
```

## 6. SECURITY (OAUTH2)

```python
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/users/me")
def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
```

## 7. MIDDLEWARE & CORS

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 8. TESTING

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
```

## 9. BACKGROUND TASKS

```python
from fastapi import BackgroundTasks

def write_notification(email: str, message: str):
    with open("log.txt", "a") as mode:
        mode.write(f"notification for {email}: {message}\n")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```
