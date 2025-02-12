import enum
from sqlalchemy import Boolean,Column, Integer, String, Text,ForeignKey,DateTime
from sqlalchemy.types import Enum as BaseEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP

from datetime import datetime,timedelta
from database import Base,get_db
from fastapi import Depends,Request,HTTPException,status
from sqlalchemy.orm import Session,relationship
from sqlalchemy.sql import func,text
from jose import JWTError,jwt

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String,unique=True)
    hashed_password = Column(String)
    refresh_token = Column(String,nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())")
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())"), 
        onupdate=text("TIMEZONE('Asia/Kolkata', now())")
    )
    patients = relationship("Patient", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.email} {self.hashed_password}"

    @classmethod
    def get_user(cls,email,db:Session):
        """Retrieve a user by email"""
        return db.query(cls).filter_by(email=email).first()
    
    @classmethod
    def verify_password(cls,plain_password,hashed_password):
        return pwd_context.verify(plain_password,hashed_password)

    @classmethod
    def create_user(cls,data,db:Session):
        encrypt_pass = cls.get_hashed_password(data.password)
        
        new_user = cls(email = data.email,hashed_password = encrypt_pass)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @classmethod    
    def authenticate_user(cls,email:str,password:str,db:Session):
        user = cls.get_user(email,db)
        if not user:
            return False
        if not cls.verify_password(plain_password=password,hashed_password=user.hashed_password):
            return False
        return user

    @classmethod
    def get_hashed_password(cls,plain_password):
        return pwd_context.hash(plain_password)

    @classmethod
    def create_access_token(cls,data: dict,expires_in: timedelta or None = None):
        from main import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES

        to_encode = data.copy()
        expire = datetime.utcnow() + expires_in if expires_in else datetime.utcnow() + timedelta(minutes=15) 

        to_encode.update({"exp":expire})

        encoded_jwt = jwt.encode(to_encode,SECRET_KEY,ALGORITHM)

        return encoded_jwt

    @classmethod
    def update_refresh_token_of_user(cls,user,refresh_token:str,db:Session):
        loggedIn_user = cls.get_user(user.email,db)

        loggedIn_user.refresh_token = refresh_token

        db.commit()
        db.refresh(loggedIn_user)

        return loggedIn_user
    
    @classmethod
    def get_current_user(cls,db,token):
        from main import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES
        from main import TokenData
        
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

        user = cls.get_user(token_data.email,db)

        if user is None:
            raise credential_exception
        
        return user



class GradeEnum(str, enum.Enum):
    M = 'M'
    F = 'F'

class DeviceStatus(str, enum.Enum):
    Active = 'Active'
    Inactive = 'Inactive'

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(BaseEnum(GradeEnum), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())")
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())"), 
        onupdate=text("TIMEZONE('Asia/Kolkata', now())")
    )


    user = relationship("User", back_populates="patients")
    heart_rate_readings = relationship("HeartRateReading", back_populates="patient",cascade="all, delete-orphan")

    @classmethod
    def get_patient(cls,id,db:Session):
        """Retrieve a Patient by id"""
        return db.query(cls).filter_by(id=id).first()

    @classmethod
    def create_patient(cls,data,db:Session):
        new_patient = cls(**data)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        return new_patient


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=True)
    status = Column(String, nullable=False, default="Active")
    created_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())")
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())"), 
        onupdate=text("TIMEZONE('Asia/Kolkata', now())")
    )


    def __repr__(self):
        return f"{self.id} {self.patient_id} {self.status} {self.created_at}"

    heart_rate_readings = relationship("HeartRateReading", back_populates="device", cascade="all, delete-orphan")

    @classmethod
    def get_device(cls,id,db:Session):
        """Retrieve a device by id"""
        return db.query(cls).filter_by(id=id).first()
    
    @classmethod
    def get_device_by_patient_id(cls,patient_id,db:Session):
        """Retrieve a device by patient_id"""
        return db.query(cls).filter_by(patient_id=patient_id).first()

    @classmethod
    def upsert_device(cls,data,db:Session):
        if data.get("id") is None:
            new_device = cls(**data)
            db.add(new_device)
        else:
            new_device = cls.get_device(data.id,db)
            if data.patient_id is not None:
                new_device.patient_id = data.patient_id
            if data.status is not None:
                new_device.status = data.status 
        db.commit()
        db.refresh(new_device)

        return new_device


class HeartRateReading(Base):
    __tablename__ = "heart_rate_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False) 
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    heart_rate = Column(Integer, nullable=False)
    recorded_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=text("TIMEZONE('Asia/Kolkata', now())")
    )

    patient = relationship("Patient", back_populates="heart_rate_readings")
    device = relationship("Device", back_populates="heart_rate_readings")

    @classmethod
    def create_heart_reading(cls,data,db:Session):
        
        device = Device.get_device(data.get("device_id"),db)

        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")

        patient = Patient.get_patient(data.get("patient_id"),db)

        if patient is None:
            raise HTTPException(status_code=404, detail="Patient not found")

        if device.patient_id != data.get("patient_id"):
            raise HTTPException(status_code=404, detail="Device belongs to someone else.")


        new_heart_rate_reading = cls(**data)

        db.add(new_heart_rate_reading)
        db.commit()
        db.refresh(new_heart_rate_reading)

        return new_heart_rate_reading