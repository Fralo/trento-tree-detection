from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel
from app.database import Base


class TreeDB(Base):
    __tablename__ = "trees"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source_file = Column(String, nullable=False)
    bbox_xmin = Column(Integer, nullable=False)
    bbox_ymin = Column(Integer, nullable=False)
    bbox_xmax = Column(Integer, nullable=False)
    bbox_ymax = Column(Integer, nullable=False)


class TreeCreate(BaseModel):
    latitude: float
    longitude: float
    source_file: str
    bbox_xmin: int
    bbox_ymin: int
    bbox_xmax: int
    bbox_ymax: int


class Tree(BaseModel):
    id: int
    latitude: float
    longitude: float
    source_file: str
    bbox_xmin: int
    bbox_ymin: int
    bbox_xmax: int
    bbox_ymax: int

    class Config:
        from_attributes = True
