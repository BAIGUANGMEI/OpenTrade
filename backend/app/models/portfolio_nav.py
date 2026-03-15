from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PortfolioNav(Base):
    __tablename__ = "portfolio_nav"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_config_id: Mapped[int] = mapped_column(ForeignKey("model_configs.id"), index=True)
    cash_balance: Mapped[float] = mapped_column(Float, default=0.0)
    positions_value: Mapped[float] = mapped_column(Float, default=0.0)
    total_nav: Mapped[float] = mapped_column(Float, default=0.0)
    daily_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
