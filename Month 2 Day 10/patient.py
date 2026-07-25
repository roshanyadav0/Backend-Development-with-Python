from fastapi import FastAPI , Path , HTTPException , Query
import json

app = FastAPI()

def load_data ():
    with open('patients.json','r') as f:
        data = json.load(f)
    return data

@app.get("/")
def hello():
    return {"message" : "Patient Management System API"}

@app.get("/about")
def about() :
    return {"message" "A fully functional api to manager your patients"}

@app.get("/view")
def view():
    return load_data()

@app.get('/patient/{patient_id}')
def view_patient(patient_id : str = Path(...,description='Id of the patient in the Db',example='P001')):
    # Loading all the patients
    data = load_data()

    if patient_id in data :
        return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found')

@app.get('/sort')
def sort_patients(sort_by : str = Query(...,description='sort on the basis of height, weight, bmi'),order : str = Query('asc',description='sort in asc or desc')):
    valid_fields = ['height','weight','bmi']
    if sort_by not in valid_fields : 
        raise HTTPException(status_code=400,detail=f'Invalid feild select from valid {valid_fields}')
    if order not in ['asc','desc'] :
        raise HTTPException(status_code=400,detail=f'Invalid feild select between asc and desc')

    data = load_data()

    sort_order = True if order=='desc' else order=='asc'

    sorted_data = sorted(data.values(),key=lambda x: x.get(sort_by,0),reverse=sort_order)

    return sorted_data