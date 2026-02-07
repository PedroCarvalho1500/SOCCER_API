from .database import Base
from sqlalchemy import Column, Integer, LargeBinary, String, ForeignKey
from sqlalchemy.orm import relationship

# Define relationships
from sqlalchemy.sql.expression import text
import time
from pydantic import field_validator


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    position = Column(String, index=True, nullable=False)
    team = Column(String, index=True, nullable=False)
    value = Column(String, index=True, nullable=False)
    photo = Column(LargeBinary, nullable=True)
    updated = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    created = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))

class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)  # Added unique constraint
    country = Column(String, index=True, nullable=False)
    
    # Define relationship to Team
    teams = relationship("Team", back_populates="league_relation")
    updated = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    created = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    logo = Column(LargeBinary, nullable=True)

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    stadium = Column(String, index=True, nullable=False)
    coach = Column(String, index=True, nullable=False)
    league = Column(String, ForeignKey("leagues.name"), nullable=False)
    logo = Column(LargeBinary, nullable=True)
    updated = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    created = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Define relationship to League
    league_relation = relationship("League", back_populates="teams")




class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    # The role can be 'admin', 'free', or other roles as needed
    role = Column(String, default="free", nullable=False)
    created_at = Column(String, index=True, nullable=False, server_default=time.strftime("%Y-%m-%d %H:%M:%S"))

    #Validate role field
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ["admin", "free", "user"]:
            raise ValueError("Role must be either 'admin' or 'free' or 'user'")
        return v


class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String, unique=True, index=True)