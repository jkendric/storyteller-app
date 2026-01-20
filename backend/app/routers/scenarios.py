from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scenario
from app.schemas import ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioList

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=ScenarioList)
def list_scenarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all scenarios with pagination."""
    scenarios = db.query(Scenario).offset(skip).limit(limit).all()
    total = db.query(Scenario).count()
    return ScenarioList(scenarios=scenarios, total=total)


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db),
):
    """Create a new scenario."""
    db_scenario = Scenario(**scenario.model_dump())
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """Get a scenario by ID."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: int,
    scenario_update: ScenarioUpdate,
    db: Session = Depends(get_db),
):
    """Update a scenario."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    update_data = scenario_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
):
    """Delete a scenario."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    db.delete(scenario)
    db.commit()
