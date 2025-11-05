from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Tree, TreeCreate, TreeDB

app = FastAPI(title="Tree Detection API", version="1.0.0")

# Configure CORS to accept requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def root():
    return {"message": "Tree Detection API - Use /trees endpoint"}


@app.get("/trees", response_model=List[Tree])
def get_trees(
    min_lat: float = None,
    max_lat: float = None,
    min_lon: float = None,
    max_lon: float = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(TreeDB)

    if min_lat is not None:
        query = query.filter(TreeDB.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(TreeDB.latitude <= max_lat)
    if min_lon is not None:
        query = query.filter(TreeDB.longitude >= min_lon)
    if max_lon is not None:
        query = query.filter(TreeDB.longitude <= max_lon)

    trees = query.limit(limit).all()
    print(f"Retrieved {len(trees)} trees from the database.")
    return trees


@app.post("/trees", response_model=Tree, status_code=201)
def create_tree(tree: TreeCreate, db: Session = Depends(get_db)):
    import os
    if os.getenv("ENV") != "development":
        raise HTTPException(status_code=403, detail="Tree creation is not allowed in production environment.")
    db_tree = TreeDB(**tree.model_dump())
    db.add(db_tree)
    db.commit()
    db.refresh(db_tree)
    return db_tree
