"""
FastAPI app called 'Bookipedia' that serves information about books and their authors. A simple example of a
"many-to-many" relationship *with* extra data. This solution uses SQLAlchemy Association Proxies
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, joinedload
from sqlalchemy.ext.associationproxy import association_proxy

# Make the engine
engine = create_engine("sqlite+pysqlite:///:memory:", future=True, echo=True,
                       connect_args={"check_same_thread": False})

# Make the DeclarativeMeta
Base = declarative_base()

# Declare Classes / Tables
class BookAuthor(Base):
    __tablename__ = 'book_authors'
    book_id = Column(ForeignKey('books.id'), primary_key=True)
    author_id = Column(ForeignKey('authors.id'), primary_key=True)
    blurb = Column(String, nullable=False)
    book = relationship("Book", back_populates="authors")
    author = relationship("Author", back_populates="books")

    # proxies
    author_name = association_proxy(target_collection='author', attr='name')
    book_title = association_proxy(target_collection='book', attr='title')

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = relationship("BookAuthor", back_populates="book")

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    books = relationship("BookAuthor", back_populates="author")

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

    session.add_all([book1, book2, author1, author2, author3])
    session.commit()

    book_author1 = BookAuthor(book_id=book1.id, author_id=author1.id, blurb="Blue wrote chapter 1")
    book_author2 = BookAuthor(book_id=book1.id, author_id=author2.id, blurb="Chip wrote chapter 2")
    book_author3 = BookAuthor(book_id=book2.id, author_id=author1.id, blurb="Blue wrote chapters 1-3")
    book_author4 = BookAuthor(book_id=book2.id, author_id=author3.id, blurb="Alyssa wrote chapter 4")

    session.add_all([book_author1, book_author2, book_author3, book_author4])
    session.commit()


from typing import List, Optional
from pydantic import BaseModel, Field

class AuthorBase(BaseModel):
    id: int = Field(alias='author_id')
    name: str = Field(alias='author_name')
    blurb: Optional[str]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class BookBase(BaseModel):
    id: int = Field(alias='book_id')
    title: str = Field(alias='book_title')
    blurb: Optional[str]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

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

@app.get("/books/{id}", response_model=BookSchema,
         response_model_exclude={'blurb'}, response_model_by_alias=False)
async def get_book(id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).options(joinedload(Book.authors)).\
        where(Book.id == id).one()
    return db_book


@app.get("/books", response_model=List[BookSchema],
         response_model_exclude={'blurb'}, response_model_by_alias=False)
async def get_books(db: Session = Depends(get_db)):
    db_books = db.query(Book).options(joinedload(Book.authors)).all()
    return db_books


@app.get("/authors/{id}", response_model=AuthorSchema,
         response_model_exclude={'blurb'}, response_model_by_alias=False)
async def get_author(id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).options(joinedload(Author.books)).\
        where(Author.id == id).one()
    return db_author


@app.get("/authors", response_model=List[AuthorSchema],
         response_model_exclude={'blurb'}, response_model_by_alias=False)
async def get_authors(db: Session = Depends(get_db)):
    db_authors = db.query(Author).options(joinedload(Author.books)).all()
    return db_authors

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)