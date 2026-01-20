from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.llm_provider import LLMProvider
from app.schemas.llm_provider import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    LLMProviderList,
    ProviderTestResult,
    ProviderModelsResponse,
)
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/providers", response_model=LLMProviderList)
def list_providers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all LLM providers with pagination."""
    providers = db.query(LLMProvider).offset(skip).limit(limit).all()
    total = db.query(LLMProvider).count()
    return LLMProviderList(providers=providers, total=total)


@router.post("/providers", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(
    provider: LLMProviderCreate,
    db: Session = Depends(get_db),
):
    """Create a new LLM provider."""
    # If this is being set as default, clear other defaults
    if provider.is_default:
        db.query(LLMProvider).filter(LLMProvider.is_default == True).update(
            {"is_default": False}
        )

    # If this is being set as alternate, clear other alternates
    if provider.is_alternate:
        db.query(LLMProvider).filter(LLMProvider.is_alternate == True).update(
            {"is_alternate": False}
        )

    db_provider = LLMProvider(**provider.model_dump())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Get a provider by ID."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/providers/{provider_id}", response_model=LLMProviderResponse)
def update_provider(
    provider_id: int,
    provider_update: LLMProviderUpdate,
    db: Session = Depends(get_db),
):
    """Update a provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_update.model_dump(exclude_unset=True)

    # Handle is_default flag - clear others if setting to True
    if update_data.get("is_default") is True:
        db.query(LLMProvider).filter(
            LLMProvider.id != provider_id,
            LLMProvider.is_default == True
        ).update({"is_default": False})

    # Handle is_alternate flag - clear others if setting to True
    if update_data.get("is_alternate") is True:
        db.query(LLMProvider).filter(
            LLMProvider.id != provider_id,
            LLMProvider.is_alternate == True
        ).update({"is_alternate": False})

    for field, value in update_data.items():
        setattr(provider, field, value)

    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Delete a provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    db.delete(provider)
    db.commit()


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Test connection to a provider and return available models."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        is_healthy = await llm_service.health_check(provider)
        if is_healthy:
            models = await llm_service.list_models(provider)
            model_names = [m.get("id") or m.get("name", "unknown") for m in models]
            return ProviderTestResult(
                status="ok",
                message="Connection successful",
                models=model_names
            )
        else:
            return ProviderTestResult(
                status="error",
                message="Provider is not responding"
            )
    except Exception as e:
        return ProviderTestResult(
            status="error",
            message=str(e)
        )


@router.get("/providers/{provider_id}/models", response_model=ProviderModelsResponse)
async def list_provider_models(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """List available models from a provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        models = await llm_service.list_models(provider)
        return ProviderModelsResponse(models=models)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch models from provider: {str(e)}"
        )


@router.post("/providers/test-url", response_model=ProviderTestResult)
async def test_provider_url(
    base_url: str,
):
    """Test connection to a provider URL without saving it."""
    from app.models.llm_provider import ProviderType

    # Create a temporary provider object for testing
    class TempProvider:
        def __init__(self, url):
            self.base_url = url
            self.provider_type = ProviderType.OLLAMA  # Type doesn't matter for URL test

    temp = TempProvider(base_url)

    try:
        is_healthy = await llm_service.health_check(temp)
        if is_healthy:
            models = await llm_service.list_models(temp)
            model_names = [m.get("id") or m.get("name", "unknown") for m in models]
            return ProviderTestResult(
                status="ok",
                message="Connection successful",
                models=model_names
            )
        else:
            return ProviderTestResult(
                status="error",
                message="Provider is not responding"
            )
    except Exception as e:
        return ProviderTestResult(
            status="error",
            message=str(e)
        )
