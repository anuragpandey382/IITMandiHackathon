from fastapi import APIRouter, HTTPException
from db.mongo import users_collection
from models.users import SignupRequest, LoginRequest
import bcrypt

router = APIRouter()

@router.post("/signup/")
def signup_user(data: SignupRequest):
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_pw = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"email": data.email, "password": hashed_pw})

    return {"message": "Email signed up successfully"}

@router.post("/login/")
def login_user(data: LoginRequest):
    user = users_collection.find_one({"email": data.email})
    if not user or not bcrypt.checkpw(data.password.encode('utf-8'), user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": f"Welcome {user['email']}!"}
