from typing import Optional
from fastapi import APIRouter, Form, Response, UploadFile, status, HTTPException, Depends
from fastapi.params import File
from sqlalchemy.orm import Session
from httpx import AsyncClient
from fastapi import BackgroundTasks, FastAPI
from .. import models
from ..database import get_db,get_players_from_db
from ..schemas import PlayerResponse
from ..oauth2 import get_current_user
import asyncio
from collections import deque
#from ..oauth2 import get_current_user

router = APIRouter(
    tags=["Players"]
)



@router.get("/players", status_code=status.HTTP_200_OK, response_model=list[PlayerResponse])
async def get_players(db: Session = Depends(get_db),current_user: int = Depends(get_current_user),limit: int = 20, skip: int = 0, starts_by: Optional[str] = "", order_by: Optional[str] = "id"):
    async with AsyncClient() as client:
        try:
            players = await asyncio.to_thread(lambda: db.query(models.Player).filter(models.Player.name.like(f"{starts_by}%")).order_by(getattr(models.Player, order_by)).offset(skip).limit(limit).all())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Error fetching Players: {e} \n Check your query parameters"
            )
        if not players:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Players found"
            )
    return players

# @router.get("/players", status_code=status.HTTP_200_OK, response_model=list[PlayerResponse])
# def get_players(db: Session = Depends(get_db),limit: int = 10, skip: int = 0, starts_by: Optional[str] = "", order_by: Optional[str] = "id",current_user: int = Depends(get_current_user)):

#     try:
#         #get players through SQL
#         #players = get_players_from_db(db.bind.raw_connection(), limit=limit, skip=skip)
#         #get players through ORM
#         players = db.query(models.Player).filter(models.Player.name.like(f"{starts_by}%")).order_by(getattr(models.Player, order_by)).offset(skip).limit(limit).all()
#         #print(f"Verbs: {verbs}")
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Error fetching Players: {e} \n Check your query parameters"
#         )
#     if not players:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="No Players found"
#         )
    
#     return players


@router.get("/players/{player_id}", status_code=status.HTTP_200_OK, response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.get("/players/{player_id}/photo", status_code=status.HTTP_200_OK)
def get_player_photo(player_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if not player.photo:
        raise HTTPException(status_code=404, detail="Player photo not found")
    return Response(content=player.photo, media_type="image/png")

@router.post("/players", status_code=status.HTTP_201_CREATED, response_model=PlayerResponse)
async def create_player(
    
    name: str = Form(...),
    position: str = Form(...),
    team: str = Form(...),
    value: str = Form(...),
    #photo optional
    photo: Optional[UploadFile] = File(None),
    #photo: UploadFile = File(None),
    db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
):
    
    #allowed_types = {"image/png", "image/jpeg", "image/webp"}


    # Validate file type
    #if not photo.content_type or "image" not in photo.content_type:
    #    raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    #Check if team exists
    team_exists = db.query(models.Team).filter(models.Team.name == team).first()
    if not team_exists:
        raise HTTPException(status_code=400, detail=f"Team '{team}' does not exist in the database.")
    # Read the file bytes
    if photo:
        file_bytes = await photo.read()

    # Get the next ID manually (like before)
    last_id = db.query(models.Player.id).order_by(models.Player.id.desc()).first()
    new_id = (last_id[0] if last_id else 0) + 1

    try:
        new_player = models.Player(
            id=new_id,
            name=name,
            position=position,
            team=team,
            value=value,
            photo=file_bytes  # store binary directly
        )
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating Player: {e}")

    return {"id": new_player.id, "name": new_player.name, "team": new_player.team, "position": new_player.position,"value": new_player.value,
            "created": new_player.created, "updated": new_player.updated}


@router.put("/players/{player_id}", status_code=status.HTTP_200_OK, response_model=PlayerResponse)
async def update_player(
    player_id: int,
    name: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    team: Optional[str] = Form(None),
    value: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if name is not None:
        player.name = name
    if position is not None:
        player.position = position
    if team is not None:
        #Check if team exists
        team_exists = db.query(models.Team).filter(models.Team.name == team).first()
        if not team_exists:
            raise HTTPException(status_code=400, detail=f"Team '{team}' does not exist in the database.")
        player.team = team
    if value is not None:
        player.value = value
    if photo is not None:
        if not photo.content_type or "image" not in photo.content_type:
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
        file_bytes = await photo.read()
        player.photo = file_bytes

    try:
        db.commit()
        db.refresh(player)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating Player: {e}")

    return player


@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    try:
        db.delete(player)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting Player: {e}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)