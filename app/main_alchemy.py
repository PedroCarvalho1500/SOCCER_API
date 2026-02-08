from typing import Optional
from fastapi import FastAPI, File, UploadFile, status, HTTPException, Depends
from fastapi.params import Form
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import connect_to_db, get_db
from starlette.middleware.base import BaseHTTPMiddleware
from .schemas import PlayerResponse, TeamResponse,LeagueResponse
from . import models
from fastapi import FastAPI, HTTPException, Request
from .database import get_db, SessionLocal, engine
from .routers import leagues,teams, players, users, auth
from jose import jwt, JWTError
from .models import User,SessionModel
import asyncio

app = FastAPI()


security = HTTPBearer()

MAX_CONCURRENT = 500
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

#@app.middleware("http")
#async def limit_concurrency(request: Request, call_next):
#    async with semaphore:
#        return await call_next(request)

#limiter = CapacityLimiter(20)
#include routers
app.include_router(leagues.router)
app.include_router(teams.router)
app.include_router(players.router)
app.include_router(users.router)
app.include_router(auth.router)
# Define role-based access control (RBAC) structure
RESOURCES_FOR_ROLES = {
    "admin": {
        "users": ["read", "write", "delete"],
        "leagues": ["read", "write", "delete"],
        "players": ["read", "write", "delete"],
        "teams": ["read", "write", "delete"]
    },
    "user": {
        "leagues": ["read"],
        "players": ["read", "write"],
        "teams": ["read", "write"]
    },
    "free":{
        "leagues": ["read"],
        "players": ["read"],
        "teams": ["read"]
    }
}




#bind sqlalchmy models



models.Base.metadata.create_all(bind=engine)






def translate_method_to_action(method: str) -> str:
    method_permission_mapping = {
        "GET": "read",
        "POST": "write",
        "PUT": "update",
        "DELETE": "delete",
    }
    return method_permission_mapping.get(method.upper(), "read")
    


def has_permission(user_role, resource_name, required_permission):
    resource_name = resource_name.split("/")[0]
    #print(f"{resource_name}")
    #print(f"{resource_name in RESOURCES_FOR_ROLES[user_role]}")
    if user_role in RESOURCES_FOR_ROLES and resource_name in RESOURCES_FOR_ROLES[user_role]:
        return required_permission in RESOURCES_FOR_ROLES[user_role][resource_name]
    return False


def get_user_from_token(token: str, db: Session):
    #print("Getting user from token")
    try:
        #print(f"Token: {token}")
        #print(db.query(SessionModel).all())
        #time.sleep(3000)
        user_id_from_session = db.query(SessionModel).filter(SessionModel.session_token == token).first()
        if user_id_from_session:
            user_id = user_id_from_session.user_id
        else:
            user_id = None
        #print(f"User ID: {user_id}")
        if user_id is None:
            #print("NOT FOUND")
            return HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        return HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        
        return HTTPException(status_code=401, detail="User not found")
    return user

#Add post users to the EXLUDED_PATHS list
PUBLIC_URIS = ["/login", "/users", "/users/", "users"]
EXLUDED_PATHS = ["redoc","docs", "openapi.json", "login", "obtain_cur_user","","/users", "/users/"]



class RBACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, sessionmaker):
        super().__init__(app)
        self.db_sessionmaker = sessionmaker

    async def dispatch(self, request: Request, call_next):
        request_method = str(request.method).upper()
        action = translate_method_to_action(request_method)
        resource = request.url.path[1:]

        if request.url.path == "/login" or request.url.path.startswith("/users"):
            return await call_next(request)

        if resource not in EXLUDED_PATHS:
            auth: str = request.headers.get("Authorization")
            if not auth:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"}
                )

            scheme, token = get_authorization_scheme_param(auth)
            if scheme.lower() != "bearer" or not token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )

            try:
                with self.db_sessionmaker() as db:
                    current_user = get_user_from_token(token, db)
            except Exception:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"}
                )
            try:
                print(f"current user {current_user}")
                print(f"User role: {current_user.role}, Resource: {resource}, Action: {action}")
                if not has_permission(current_user.role, resource, action):
                    print(f"User role: {current_user.role} does not have {action} permission on {resource}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Insufficient permissions"}
                    )
            except Exception as e:
                #print("ERROR")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": f"Error checking permissions or Token Expired!"}
                )

        return await call_next(request)
    
      

app.add_middleware(RBACMiddleware, sessionmaker=SessionLocal)

@app.get("/")
def home():
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1')) 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
    return {"Welcome to the SOCCER API!"}




#uvicorn main:app --reload
#uvicorn app.main_alchemy:app --reload