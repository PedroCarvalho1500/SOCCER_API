from typing import Optional
from fastapi import APIRouter, Form, Response, UploadFile, status, HTTPException, Depends
from fastapi.params import File
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..schemas import TeamResponse
from ..oauth2 import get_current_user
#from ..oauth2 import get_current_user
import asyncio
from httpx import AsyncClient

router = APIRouter(
    tags=["Teams"]
)

request_queue = asyncio.Queue()


# @router.get("/teams", status_code=status.HTTP_200_OK, response_model=list[TeamResponse])
# async def get_players(db: Session = Depends(get_db),current_user: int = Depends(get_current_user),limit: int = 20, skip: int = 0, starts_by: Optional[str] = "", order_by: Optional[str] = "id"):
#     async with AsyncClient() as client:
#         try:
#             teams = await asyncio.to_thread(lambda: db.query(models.Team).filter(models.Team.name.like(f"{starts_by}%")).order_by(getattr(models.Team, order_by)).offset(skip).limit(limit).all())

#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail=f"Error fetching teams: {e} \n Check your query parameters"
#             )
#         if not teams:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="No teams found"
#             )
#     return teams


@router.get("/teams", status_code=status.HTTP_200_OK, response_model=list[TeamResponse])
def get_teams(db: Session = Depends(get_db),current_user: int = Depends(get_current_user),limit: int = 20, skip: int = 0, starts_by: Optional[str] = "", order_by: Optional[str] = "id"):

    try:
        teams = db.query(models.Team).filter(models.Team.name.like(f"{starts_by}%")).order_by(getattr(models.Team, order_by)).offset(skip).limit(limit).all()
        
        #print(f"Verbs: {verbs}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error fetching Teams: {e} \n Check your query parameters"
        )
    if not teams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Teams found"
        )
    
    return teams


@router.get("/teams/{team_id}", status_code=status.HTTP_200_OK, response_model=TeamResponse)
def get_player(team_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/teams/{team_id}/logo", status_code=status.HTTP_200_OK)
def get_player_photo(team_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not team.logo:
        raise HTTPException(status_code=404, detail="Team logo not found")
    return Response(content=team.logo, media_type="image/png")


@router.post("/teams", status_code=status.HTTP_201_CREATED, response_model=TeamResponse)
async def create_team(name: str = Form(...),
                      stadium: str = Form(...),
                      coach: str = Form(...),
                      league: str = Form(...),
                      logo: UploadFile = File(None),
                      db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
                      ):
    
    # Validate file type
    if not logo.content_type or "image" not in logo.content_type:
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")
    # Read the file bytes
    file_bytes = await logo.read()
    last_id = db.query(models.Team.id).order_by(models.Team.id.desc()).first()
    new_id = (last_id[0] if last_id else 0) + 1
    try:
        new_team = models.Team(
            id=new_id,
            name=name,
            stadium=stadium,
            coach=coach,
            league=league,
            logo=file_bytes  # store binary directly
        )
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating Team: {e}")

    return {"id": new_team.id, "name": new_team.name, "stadium": new_team.stadium, "coach": new_team.coach, "league": new_team.league,
            "created": new_team.created, "updated": new_team.updated}

@router.put("/teams/{team_id}", status_code=status.HTTP_200_OK, response_model=TeamResponse)
async def update_team(
    team_id: int,
    name: Optional[str] = Form(None),
    stadium: Optional[str] = Form(None),
    coach: Optional[str] = Form(None),
    league: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if name is not None:
        team.name = name
    if stadium is not None:
        team.stadium = stadium
    if coach is not None:
        team.coach = coach
    if league is not None:
        team.league = league
    if logo is not None:
        if not logo.content_type or "image" not in logo.content_type:
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
        file_bytes = await logo.read()
        team.logo = file_bytes

    try:
        db.commit()
        db.refresh(team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating Team: {e}")

    return team




@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    print("Deleting team")
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    try:
        db.delete(team)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting Team: {e}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
