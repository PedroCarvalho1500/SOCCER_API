from jose import JWTError, ExpiredSignatureError, jwt
from datetime import datetime, timedelta
from .schemas import TokenData
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import database

from sqlalchemy.orm import Session
from . import models
from .config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = f"{settings.SECRET_KEY}"
ALGORITHM = f"{settings.ALGORITHM}"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return TokenData(id=user_id)

    except ExpiredSignatureError:
        print("Token expired")
        raise credentials_exception

    except JWTError:
        print("Invalid token")
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = verify_token(token, credentials_exception)
        db.query(models.User).filter(models.User.id == token.id).first()
        
        user = db.query(models.User).filter(models.User.id == token.id).first()
        #print(f"User: {user}")
        return user
    except Exception as e:
        #DELETE SESSION FROM DATABASE
        #print("Exception: Invalid token")
        session = db.query(models.SessionModel).filter(models.SessionModel.session_token == token).first()
        if session:
            db.delete(session)
            db.commit()
        raise credentials_exception
