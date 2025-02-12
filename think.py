from fastapi import FastAPI, HTTPException, Depends, APIRouter
import os
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
SQLALCHEMY_DATABASE_URL = os.getenv("postgresql://postgres:mzJriHCeFPVLDhkUvGpdqdMgyuAkpjLF@junction.proxy.rlwy.net:41933/railway")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Existing base model
class BaseTable(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    content = Column(String)
    text = Column(String, nullable=True)
    is_boolean = Column(Boolean, nullable=True)

# Original tables
class Table1(BaseTable):
    __tablename__ = "table1"

class Table2(BaseTable):
    __tablename__ = "table2"

class Table3(BaseTable):
    __tablename__ = "table3"

# New custom table
class CustomTable(Base):
    __tablename__ = "custom_table"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)

# New Questions Table
class QuestionTable(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_text = Column(String)
    answer1 = Column(String)
    answer2 = Column(String)
    answer3 = Column(String)
    answer4 = Column(String)
    correct_answer = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic models for original tables
class BaseCreate(BaseModel):
    title: str
    content: str
    text: Optional[str] = None
    is_boolean: Optional[bool] = None

class BaseResponse(BaseCreate):
    id: int

    class Config:
        orm_mode = True

# Pydantic models for custom table
class CustomCreate(BaseModel):
    name: str

class CustomResponse(CustomCreate):
    id: int

    class Config:
        orm_mode = True

# Pydantic models for questions table
class QuestionCreate(BaseModel):
    question_text: str
    answer1: str
    answer2: str
    answer3: str
    answer4: str
    correct_answer: str

class QuestionResponse(QuestionCreate):
    id: int

    class Config:
        orm_mode = True

# CRUD Utilities
class CRUD:
    def create(self, db: Session, model, schema):
        db_item = model(**schema.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def get_all(self, db: Session, model):
        return db.query(model).all()

    def get_by_id(self, db: Session, model, id: int):
        item = db.query(model).filter(model.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    def update(self, db: Session, model, id: int, schema):
        db_item = self.get_by_id(db, model, id)
        for key, value in schema.dict().items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
        return db_item

    def delete(self, db: Session, model, id: int):
        db_item = self.get_by_id(db, model, id)
        db.delete(db_item)
        db.commit()
        return {"message": "Item deleted successfully"}

crud = CRUD()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_router(table_model, tag_name):
    router = APIRouter(tags=[tag_name])

    @router.post("/", response_model=BaseResponse)
    def create_item(item: BaseCreate, db: Session = Depends(get_db)):
        return crud.create(db, table_model, item)

    @router.get("/", response_model=list[BaseResponse])
    def read_all_items(db: Session = Depends(get_db)):
        return crud.get_all(db, table_model)

    @router.get("/{item_id}", response_model=BaseResponse)
    def read_item(item_id: int, db: Session = Depends(get_db)):
        return crud.get_by_id(db, table_model, item_id)

    @router.put("/{item_id}", response_model=BaseResponse)
    def update_item(item_id: int, item: BaseCreate, db: Session = Depends(get_db)):
        return crud.update(db, table_model, item_id, item)

    @router.delete("/{item_id}")
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        return crud.delete(db, table_model, item_id)

    return router

# Custom router for new table
def create_custom_router():
    router = APIRouter(tags=["Custom Table"])

    @router.post("/", response_model=CustomResponse)
    def create_item(item: CustomCreate, db: Session = Depends(get_db)):
        return crud.create(db, CustomTable, item)

    @router.get("/", response_model=list[CustomResponse])
    def read_all_items(db: Session = Depends(get_db)):
        return crud.get_all(db, CustomTable)

    @router.get("/{item_id}", response_model=CustomResponse)
    def read_item(item_id: int, db: Session = Depends(get_db)):
        return crud.get_by_id(db, CustomTable, item_id)

    @router.put("/{item_id}", response_model=CustomResponse)
    def update_item(item_id: int, item: CustomCreate, db: Session = Depends(get_db)):
        return crud.update(db, CustomTable, item_id, item)

    @router.delete("/{item_id}")
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        return crud.delete(db, CustomTable, item_id)

    return router

# Router for questions table
def create_question_router():
    router = APIRouter(tags=["Questions"])

    @router.post("/", response_model=QuestionResponse)
    def create_question(item: QuestionCreate, db: Session = Depends(get_db)):
        return crud.create(db, QuestionTable, item)

    @router.get("/", response_model=list[QuestionResponse])
    def read_all_questions(db: Session = Depends(get_db)):
        return crud.get_all(db, QuestionTable)

    @router.get("/{item_id}", response_model=QuestionResponse)
    def read_question(item_id: int, db: Session = Depends(get_db)):
        return crud.get_by_id(db, QuestionTable, item_id)

    @router.put("/{item_id}", response_model=QuestionResponse)
    def update_question(item_id: int, item: QuestionCreate, db: Session = Depends(get_db)):
        return crud.update(db, QuestionTable, item_id, item)

    @router.delete("/{item_id}")
    def delete_question(item_id: int, db: Session = Depends(get_db)):
        return crud.delete(db, QuestionTable, item_id)

    return router

# Include all routers
app.include_router(create_router(Table1, "table1"), prefix="/table1")
app.include_router(create_router(Table2, "table2"), prefix="/table2")
app.include_router(create_router(Table3, "table3"), prefix="/table3")
app.include_router(create_custom_router(), prefix="/custom")
app.include_router(create_question_router(), prefix="/questions")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

