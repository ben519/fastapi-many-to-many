"""
FastAPI app called 'Bookipedia' that serves information about books and their authors. A simple example of a
"many-to-many" relationship *with* extra data. This solution uses SQLAlchemy view only descriptor
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, object_session

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

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    @property
    def authors(self):
        s = """
            SELECT temp.* FROM (
                SELECT
                    authors.*,
                    book_authors.blurb,
                    book_authors.book_id
                FROM authors INNER JOIN book_authors ON authors.id = book_authors.author_id
            ) AS temp
            INNER JOIN books ON temp.book_id = books.id
            WHERE books.id = :bookid
            """
        result = object_session(self).execute(s, params={'bookid': self.id}).fetchall()
        return result

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @property
    def books(self):
        s = """
            SELECT temp.* FROM (
                SELECT
                    books.*,
                    book_authors.blurb,
                    book_authors.author_id
                FROM books INNER JOIN book_authors ON books.id = book_authors.book_id
            ) AS temp
            INNER JOIN authors ON temp.author_id = authors.id
            WHERE authors.id = :authorid
            """
        result = object_session(self).execute(s, params={'authorid': self.id}).fetchall()
        return result

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
    db_book = db.query(Book).where(Book.id == id).one()
    return db_book


@app.get("/books", response_model=List[BookSchema])
async def get_books(db: Session = Depends(get_db)):
    db_books = db.query(Book).all()
    return db_books


@app.get("/authors/{id}", response_model=AuthorSchema)
async def get_author(id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).where(Author.id == id).one()
    return db_author


@app.get("/authors", response_model=List[AuthorSchema])
async def get_authors(db: Session = Depends(get_db)):
    db_authors = db.query(Author).all()
    return db_authors


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)