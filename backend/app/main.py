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
def get_trees(db: Session = Depends(get_db)):
    trees = db.query(TreeDB).all()
    return trees


@app.post("/trees", response_model=Tree, status_code=201)
def create_tree(tree: TreeCreate, db: Session = Depends(get_db)):
    db_tree = TreeDB(**tree.model_dump())
    db.add(db_tree)
    db.commit()
    db.refresh(db_tree)
    return db_tree
