from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.speed_button import SpeedButton
from app.schemas.speed_button import (
    SpeedButtonCreate,
    SpeedButtonUpdate,
    SpeedButtonResponse,
    SpeedButtonList,
    SpeedButtonReorder,
)

router = APIRouter(prefix="/api/speed-buttons", tags=["speed-buttons"])


@router.get("", response_model=SpeedButtonList)
def list_speed_buttons(db: Session = Depends(get_db)):
    """List all speed buttons ordered by display_order."""
    buttons = db.query(SpeedButton).order_by(SpeedButton.display_order).all()
    return SpeedButtonList(speed_buttons=buttons, total=len(buttons))


@router.post("", response_model=SpeedButtonResponse, status_code=status.HTTP_201_CREATED)
def create_speed_button(
    button: SpeedButtonCreate,
    db: Session = Depends(get_db),
):
    """Create a new speed button."""
    # Get max display_order if not specified
    if button.display_order is None or button.display_order == 0:
        max_order = db.query(SpeedButton.display_order).order_by(
            SpeedButton.display_order.desc()
        ).first()
        display_order = (max_order[0] + 1) if max_order else 0
    else:
        display_order = button.display_order

    db_button = SpeedButton(
        label=button.label,
        guidance=button.guidance,
        use_alternate=button.use_alternate,
        display_order=display_order,
        is_default=False,
    )
    db.add(db_button)
    db.commit()
    db.refresh(db_button)
    return db_button


@router.get("/{button_id}", response_model=SpeedButtonResponse)
def get_speed_button(
    button_id: int,
    db: Session = Depends(get_db),
):
    """Get a speed button by ID."""
    button = db.query(SpeedButton).filter(SpeedButton.id == button_id).first()
    if not button:
        raise HTTPException(status_code=404, detail="Speed button not found")
    return button


@router.put("/{button_id}", response_model=SpeedButtonResponse)
def update_speed_button(
    button_id: int,
    button_update: SpeedButtonUpdate,
    db: Session = Depends(get_db),
):
    """Update a speed button."""
    button = db.query(SpeedButton).filter(SpeedButton.id == button_id).first()
    if not button:
        raise HTTPException(status_code=404, detail="Speed button not found")

    update_data = button_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(button, field, value)

    db.commit()
    db.refresh(button)
    return button


@router.delete("/{button_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_speed_button(
    button_id: int,
    db: Session = Depends(get_db),
):
    """Delete a speed button."""
    button = db.query(SpeedButton).filter(SpeedButton.id == button_id).first()
    if not button:
        raise HTTPException(status_code=404, detail="Speed button not found")

    # Prevent deleting default buttons
    if button.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default speed buttons"
        )

    db.delete(button)
    db.commit()


@router.post("/reorder", response_model=SpeedButtonList)
def reorder_speed_buttons(
    reorder: SpeedButtonReorder,
    db: Session = Depends(get_db),
):
    """Reorder speed buttons by providing a list of IDs in the desired order."""
    # Verify all buttons exist
    buttons = db.query(SpeedButton).filter(
        SpeedButton.id.in_(reorder.button_ids)
    ).all()

    if len(buttons) != len(reorder.button_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more button IDs are invalid"
        )

    # Update display_order based on position in list
    button_map = {b.id: b for b in buttons}
    for index, button_id in enumerate(reorder.button_ids):
        button_map[button_id].display_order = index

    db.commit()

    # Return updated list
    all_buttons = db.query(SpeedButton).order_by(SpeedButton.display_order).all()
    return SpeedButtonList(speed_buttons=all_buttons, total=len(all_buttons))
