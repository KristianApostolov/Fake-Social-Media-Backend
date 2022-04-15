from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
import random
import datetime
from sqlalchemy import null
from database import *
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime
from fastapi.responses import JSONResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@AuthJWT.load_config
def get_config():
    return Config()


def get_user(username: str):
    with Session(engine) as db:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return user
        else:
            return False


def password_hasher(password:str):
    return pwd_context.hash(password)


def credential_check(username, email):
    with Session(engine) as db:
        user_by_email = db.query(User).filter(User.email == email).first()
        user_by_username = db.query(User).filter(User.email == username).first()
    if not user_by_username and not user_by_email:
        return True
    else:
        return False

def password_verify(password : str, hashed_password : str):
    verified = pwd_context.verify(password,hashed_password)
    print(verified)
    if verified:
        return True
    return False

def new_user_assignment(email:str,username:str,password:str):
    randint = random.randint(1111,9999)
    new_user = User(
        email=email,
        password=password_hasher(password),
        usertag=username+'@'+f'{randint}',
        username=username,
        timejoined=datetime.now(),
        last_seen=datetime.now(),
        online=True
    )
    with Session(engine) as db:
        db.add(new_user)
        db.commit()
    print('REGISTERED NEW USER:',username, 'AT:',datetime.now())
