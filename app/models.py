from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, Text, Index


class Base(DeclarativeBase):
    pass


class TestCase(Base):
    __tablename__ = "test_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class TestRun(Base):
    __tablename__ = "test_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    results: Mapped[list["TestResult"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class TestResult(Base):
    __tablename__ = "test_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("test_run.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(512), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    run: Mapped["TestRun"] = relationship(back_populates="results")
