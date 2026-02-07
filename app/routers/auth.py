from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import database, oauth2
from .. import models
from ..schemas import Token
from ..utils import verify_password
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials"
        )
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")

    access_token = oauth2.create_access_token(data={"user_id": user.id})
    #print(f"access_token: {access_token}")
    session = models.SessionModel(user_id=user.id, session_token=access_token)
    
    #Update the session token in the database
    existing_session = db.query(models.SessionModel).filter(models.SessionModel.user_id == user.id).first()
    # If an existing session is found, update the session token
    if existing_session:
        #print("WENT THROUGH SESSION UPDATE")
        existing_session.session_token = access_token
        db.commit()
        db.refresh(existing_session)
        return {"access_token": existing_session.session_token, "token_type": "bearer"}
    # If no existing session, create a new one
    
    #Delete all existing sessions
    db.query(models.SessionModel).filter(models.SessionModel.user_id > 0).delete()
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"access_token": access_token, "token_type": "bearer"}
  