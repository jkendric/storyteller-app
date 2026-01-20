from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Character
from app.schemas import CharacterCreate, CharacterUpdate, CharacterResponse, CharacterList

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("", response_model=CharacterList)
def list_characters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all characters with pagination."""
    characters = db.query(Character).offset(skip).limit(limit).all()
    total = db.query(Character).count()
    return CharacterList(characters=characters, total=total)


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(
    character: CharacterCreate,
    db: Session = Depends(get_db),
):
    """Create a new character."""
    db_character = Character(**character.model_dump())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(
    character_id: int,
    db: Session = Depends(get_db),
):
    """Get a character by ID."""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
def update_character(
    character_id: int,
    character_update: CharacterUpdate,
    db: Session = Depends(get_db),
):
    """Update a character."""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    update_data = character_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    db.commit()
    db.refresh(character)
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: int,
    db: Session = Depends(get_db),
):
    """Delete a character."""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    db.delete(character)
    db.commit()
