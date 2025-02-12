import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends,Response,Request,status,Header
from pydantic import BaseModel,EmailStr
from typing import List,Annotated
from datetime import datetime,timedelta
import uuid
import models
from fastapi.security import OAuth2PasswordBearer
from models import User,Patient,Device,HeartRateReading
from database import engine,get_db
from sqlalchemy.orm import Session,joinedload
from jose import JWTError,jwt
from typing import Optional
from sqlalchemy import desc

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()


# db_dependency = Annotated[Session,Depends(get_db)]

class UserSchema(BaseModel):
    email:EmailStr
    password:str

class TokenData(BaseModel):
    email: EmailStr or None = None

class Token(BaseModel):
    user: TokenData
    access_token: str
    token_type: str
    refresh_token: str

def get_token(request: Request):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]

    if not token:
        token = request.cookies.get("accessToken")
    
    if not token:
        raise HTTPException(status_code=401, detail="No valid token found")

    return token

def get_device_id(request:Request,device_id: str = Header(...)):

    if not device_id:
        raise HTTPException(status_code=401, detail="device-id not found in headers")
    
    if not device_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid device ID format")

    return device_id
        


async def get_current_user(token:str = Depends(get_token)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="could not validate credentials",
                                        headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token,SECRET_KEY,ALGORITHM)
        email:str = payload.get('sub')
        if email is None:
            raise credential_exception
        
        token_data = TokenData(email = email)

    except JWTError:
        raise credential_exception

    db_session = next(get_db())
    user = User.get_user(token_data.email,db_session)

    if user is None:
        raise credential_exception
    
    return user


@app.get("/")
def ready():
    return {"message":"ready"}

@app.post('/register')
def register_user(user:UserSchema, db: Session = Depends(get_db)):
    new_user = User.create_user(user,db)
    return {"message": "User created successfully", "user": new_user.email}

@app.post("/token",response_model=Token)
async def login_for_access_token(response:Response,
                                form_data:UserSchema,
                                db: Session = Depends(get_db)):
    user = User.authenticate_user(form_data.email,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate":"Bearer"})
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = User.create_access_token(data={"sub":user.email},expires_in=access_token_expires)
    refresh_token = User.create_access_token(data={"sub":user.email},expires_in=timedelta(days=1))

    user = User.update_refresh_token_of_user(user,refresh_token,db)

    response.set_cookie(
    key="accessToken",
    value=access_token,
    httponly=True,
    secure=True,
    samesite="Lax",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    )

    user = TokenData(email = user.email)

    return {"user":user,"access_token":access_token,"token_type":"bearer","refresh_token":refresh_token}

@app.post("/logout")
def logout(response:Response,token:str = Depends(get_token),db:Session = Depends(get_db)):

    try:
        user = User.get_current_user(db,token)
        if user:
            user = User.update_refresh_token_of_user(user,None,db)

        response.delete_cookie("accessToken")
        response.delete_cookie("refreshToken")

        response.headers["WWW-Authenticate"] = 'Bearer realm="invalid_token"'
    
    except:
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    return {"message":"Loggged out successfully"}


class PatientResSchema(BaseModel):
    id:int
    name:str
    age:int
    user_id:int
    device_id:Optional[int] = None

class HeartReadingSchema(BaseModel):
    patient_id:int
    heart_rate:int

class HeartReadingResSchema(HeartReadingSchema):
    id:int
    device_id:int
    created_at:datetime

class PatientSchema(BaseModel):
    name:str
    age:int
    gender:str

@app.post("/patients/add_patients",response_model=PatientResSchema)
def add_patient(patient:PatientSchema, db: Session = Depends(get_db),user: User = Depends(get_current_user)):
    patient_data = patient.dict()
    patient_data["user_id"] = user.id

    new_patient = Patient.create_patient(patient_data,db)

    return new_patient

class HeartReadingSchema(BaseModel):
    patient_id:int
    heart_rate:int

class HeartReadingResSchema(HeartReadingSchema):
    id:int
    device_id:int
    recorded_at:datetime

class PatientGetResSchema(BaseModel):
    id : int
    name : str
    age : int
    gender : str
    user_id : int
    created_at:datetime
    heart_rate_readings :List[HeartReadingResSchema]

class PatientGetResSchema1(PatientGetResSchema):
    device_id: Optional[int] = None


@app.get("/patients/get-patients",response_model=List[PatientGetResSchema])
def get_all_patients(db: Session = Depends(get_db),user:User = Depends(get_current_user)):
    patients = db.query(Patient).all()

    for patient in patients:
        patient.heart_rate_readings = (
            db.query(HeartRateReading)
            .filter(HeartRateReading.patient_id == patient.id)            
            .order_by(desc(HeartRateReading.recorded_at))
            .limit(2)
            .all()
        )

    return patients

@app.get("/heart-readings/{patient_id}",response_model=PatientGetResSchema1)
def get_patients_heart_readings(patient_id:int,db: Session = Depends(get_db),user:User = Depends(get_current_user)):
    patient = Patient.get_patient(patient_id,db) 

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    device = Device.get_device_by_patient_id(patient.id, db)

    patient_data = patient.__dict__.copy()
    patient_data["device_id"] = device.id if device else None

    patient_data["heart_rate_readings"] = sorted(
        patient.heart_rate_readings, key=lambda x: x.recorded_at, reverse=True
    )
    
    return patient_data
    


class DeviceReqSchema(BaseModel):
    patient_id: int
    status: str

class DeviceResSchema(DeviceReqSchema):
    id: int
    created_at: datetime

@app.post("/devices/add_devices",response_model=DeviceResSchema)
def add_device(device:DeviceReqSchema, db: Session = Depends(get_db),user:User = Depends(get_current_user)):
    device = Device.upsert_device(device.dict(),db)
    return device


@app.post("/heart_readings",response_model=HeartReadingResSchema)
def create_heart_reading(
    data: HeartReadingSchema,db: Session = Depends(get_db),
    device_id: str = Depends(get_device_id)):
    
    data = data.dict()
    data['device_id'] = device_id

    reading = HeartRateReading.create_heart_reading(data,db)

    return reading
