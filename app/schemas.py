


from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

"""class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)  # Added unique constraint
    country = Column(String, index=True, nullable=False)
    
    # Define relationship to Team
    teams = relationship("Team", back_populates="league_relation")
    updated = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    created = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    logo = Column(LargeBinary, nullable=True)"""

class LeagueBase(BaseModel):
    id: Optional[int] = None
    name: str
    country: str
    logo: Optional[bytes] = None
    updated: Optional[str] = None
    created: Optional[str] = None

class CreateLeague(LeagueBase):
    pass


class UpdateLeague(BaseModel):
    pass


class LeagueResponse(BaseModel):
    id: int
    name: str
    country: str
    created: str
    updated: str

    class Config:
        orm_mode = True


class TeamBase(BaseModel):
    id: Optional[int] = None
    name: str
    stadium: str
    coach: str
    league: str
    logo: Optional[bytes] = None
    updated: Optional[str] = None
    created: Optional[str] = None

class CreateTeam(TeamBase):
    pass

class UpdateTeam(BaseModel):
    pass

class TeamResponse(BaseModel):
    id: int
    name: str
    stadium: str
    coach: str
    league: str
    created: str
    updated: str

    class Config:
        orm_mode = True


class PlayerBase(BaseModel):
    id: Optional[int] = None
    name: str
    position: str
    team: str
    value: str
    photo: Optional[bytes] = None
    updated: Optional[str] = None
    created: Optional[str] = None

class CreatePlayer(PlayerBase):
    pass

class UpdatePlayer(BaseModel):
    pass

class PlayerResponse(BaseModel):
    id: int
    name: str
    team: str
    position: str
    value: str
    updated: str
    created: str

    class Config:
        orm_mode = True



class UserBase(BaseModel):
    username: EmailStr
    password: str
    created_at: Optional[str] = None
    role: str

class UserCreate(UserBase):
    pass

    @validator('role')
    def validate_role(cls, v):
        if v not in ["admin", "free", "user"]:
            raise ValueError("Role must be either 'admin', 'free', or 'user'")
        return v


class UserLogin(BaseModel):
    username: EmailStr
    password: str

class UserUpdate(UserBase):
    pass

class UserResponse(BaseModel):
    id: int
    username: EmailStr
    created_at: str
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None