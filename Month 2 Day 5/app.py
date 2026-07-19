from fastapi import FastAPI
from pprint import pprint

app = FastAPI()

data = {
    "name": "John Doe",
    "age": 30,
}

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/get_data")
def get_data():
    res = data
    pprint(type(res))
    return res

