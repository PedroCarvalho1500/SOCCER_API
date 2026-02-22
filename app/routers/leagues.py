from typing import Optional
from fastapi import APIRouter, Form, Response, UploadFile, status, HTTPException, Depends
from fastapi.params import File
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..schemas import LeagueResponse
from ..oauth2 import get_current_user
#from ..oauth2 import get_current_user
#from ..main_alchemy import limiter
from fastapi import BackgroundTasks
import asyncio

router = APIRouter(
    tags=["Leagues"]
)


#heavy_sem = asyncio.Semaphore(10)


#Get leagues with heavy_sem
# @router.get("/leagues", status_code=status.HTTP_200_OK,response_model=list[LeagueResponse])
# async def get_leagues(db: Session = Depends(get_db), current_user: int = Depends(get_current_user), limit: int = 20, skip: int = 0, starts_by: Optional[str] = "", order_by: Optional[str] = "id"):
#     async with heavy_sem:
#         try:
#             leagues = db.query(models.League).filter(models.League.name.like(f"{starts_by}%")).order_by(getattr(models.League, order_by)).offset(skip).limit(limit).all()
            
#             #print(f"Verbs: {verbs}")
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail=f"Error fetching Leagues: {e} \n Check your query parameters"
#             )
#         if not leagues:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="No Leagues found"
#             )
        
#         return leagues

 
@router.get("/leagues", status_code=status.HTTP_200_OK,response_model=list[LeagueResponse])
def get_leagues(db: Session = Depends(get_db),current_user: int = Depends(get_current_user),limit: int = 20, skip: int = 0, starts_by: Optional[str] = "",l_country: Optional[str] = "", order_by: Optional[str] = "id", background_tasks: BackgroundTasks = None):

    try:
        leagues = db.query(models.League).filter(
            models.League.name.like(f"{starts_by}%"),
            models.League.country.like(f"%{l_country}%")
        ).order_by(getattr(models.League, order_by)).offset(skip).limit(limit).all()
        
        #print(f"Verbs: {verbs}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error fetching Leagues: {e} \n Check your query parameters"
        )
    if not leagues:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Leagues found"
        )
    
    return leagues




# @router.get("/leagues", status_code=status.HTTP_200_OK,response_model=list[LeagueResponse])
# async def get_leagues(db: Session = Depends(get_db),current_user: int = Depends(get_current_user),limit: int = 20, skip: int = 0, starts_by: Optional[str] = "",l_country: Optional[str] = "", order_by: Optional[str] = "id", background_tasks: BackgroundTasks = None):

#     try:
#         leagues = db.query(models.League).filter(
#             models.League.name.like(f"{starts_by}%"),
#             models.League.country.like(f"%{l_country}%")
#         ).order_by(getattr(models.League, order_by)).offset(skip).limit(limit).all()
        
#         #print(f"Verbs: {verbs}")
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Error fetching Leagues: {e} \n Check your query parameters"
#         )
#     if not leagues:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="No Leagues found"
#         )
    
#     return leagues



@router.post("/leagues", status_code=status.HTTP_201_CREATED)
async def create_league(
    name: str = Form(...),
    country: str = Form(...),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
):
    # Validate file type
    if not logo.content_type or "image" not in logo.content_type:
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")
    # Read the file bytes
    file_bytes = await logo.read()
    last_id = db.query(models.League.id).order_by(models.League.id.desc()).first()
    new_id = (last_id[0] if last_id else 0) + 1
    try:
        new_league = models.League(
            id=new_id,
            name=name,
            country=country,
            logo=file_bytes  # store binary directly
        )
        db.add(new_league)
        db.commit()
        db.refresh(new_league)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating League: {e}")
    return {"id": new_league.id, "name": new_league.name, "country": new_league.country,
            "created": new_league.created, "updated": new_league.updated}


@router.get("/leagues/{league_id}", status_code=status.HTTP_200_OK, response_model=LeagueResponse)
def get_player(league_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league


@router.get("/leagues/{league_id}/logo", status_code=status.HTTP_200_OK)
async def get_league_logo(league_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if not league or not league.logo:
        raise HTTPException(status_code=404, detail="League or logo not found")
    return Response(content=league.logo, media_type="image/png")


@router.put("/leagues/{league_id}", status_code=status.HTTP_200_OK)
async def update_league(
    league_id: int,
    name: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),current_user: int = Depends(get_current_user)
):
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if name is not None:
        league.name = name
    if country is not None:
        league.country = country
    if logo is not None:
        if "image" not in logo.content_type:
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
        league.logo = await logo.read()
    
    try:
        db.commit()
        db.refresh(league)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating League: {e}")
    
    return {"id": league.id, "name": league.name, "country": league.country,
            "created": league.created, "updated": league.updated}



@router.delete("/leagues/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(league_id: int, db: Session = Depends(get_db),current_user: int = Depends(get_current_user)):
    league = db.query(models.League).filter(models.League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    try:
        db.delete(league)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting League: {e}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)