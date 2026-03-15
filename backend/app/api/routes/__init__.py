from fastapi import APIRouter

from app.api.routes import decisions, market, models, portfolio, strategies

api_router = APIRouter()
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
