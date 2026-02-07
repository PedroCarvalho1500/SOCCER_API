from time import time
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from ..utils import hash_password
from .. import models
from ..database import get_db
from ..schemas import UserCreate, UserResponse
from ..oauth2 import get_current_user

router = APIRouter(
    tags=["Users"]
)





@router.post("/users/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    # has the password
    password = hash_password(user.password)
    user.password = password
    
    number_of_admins = db.query(models.User).filter(models.User.role == "admin").count()
    if number_of_admins > 0 and user.role == "admin":
        user.role = "free"

    try:
        new_user = models.User(username=user.username, password=user.password, role=user.role)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    finally:
        db.close()
    

@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user
    