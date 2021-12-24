"""
FastAPI app called 'bookipedia' that serves information about books and their authors. A simple example of a
"many-to-many" relationship *without* extra data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, joinedload

# Make the engine
engine = create_engine("sqlite+pysqlite:///:memory:", future=True, echo=True,
                       connect_args={"check_same_thread": False})

# Make the DeclarativeMeta
Base = declarative_base()

# Declare Classes / Tables
book_authors = Table('book_authors', Base.metadata,
    Column('book_id', ForeignKey('books.id'), primary_key=True),
    Column('author_id', ForeignKey('authors.id'), primary_key=True)
)

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = relationship("Author", secondary=book_authors, back_populates='books')

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    books = relationship("Book", secondary=book_authors, back_populates='authors')

# Create the tables in the database
Base.metadata.create_all(engine)


# Insert data
from sqlalchemy.orm import Session
with Session(bind=engine) as session:
    book1 = Book(title="Dead People Who'd Be Influencers Today")
    book2 = Book(title="How To Make Friends In Your 30s")

    author1 = Author(name="Blu Renolds")
    author2 = Author(name="Chip Egan")
    author3 = Author(name="Alyssa Wyatt")

    book1.authors = [author1, author2]
    book2.authors = [author1, author3]

    session.add_all([book1, book2, author1, author2, author3])
    session.commit()


from typing import List
from pydantic import BaseModel


class AuthorBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class BookBase(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True

class BookSchema(BookBase):
    authors: List[AuthorBase]

class AuthorSchema(AuthorBase):
    books: List[BookBase]


from fastapi import FastAPI, Depends

app = FastAPI(title="Bookipedia")

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

@app.get("/books/{id}", response_model=BookSchema)
async def get_book(id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).options(joinedload(Book.authors)).\
        where(Book.id == id).one()
    return db_book


@app.get("/books", response_model=List[BookSchema])
async def get_books(db: Session = Depends(get_db)):
    db_books = db.query(Book).options(joinedload(Book.authors)).all()
    return db_books


@app.get("/authors/{id}", response_model=AuthorSchema)
async def get_author(id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).options(joinedload(Author.books)).\
        where(Author.id == id).one()
    return db_author


@app.get("/authors", response_model=List[AuthorSchema])
async def get_authors(db: Session = Depends(get_db)):
    db_authors = db.query(Author).options(joinedload(Author.books)).all()
    return db_authors


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)