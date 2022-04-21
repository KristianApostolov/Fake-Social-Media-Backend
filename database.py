from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker,relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Integer, DateTime, Column

#Database
DB_NAME = 'database.db'
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

#db tables:
class User(Base):
    __tablename__ = 'userlist'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    username = Column(String(30),unique=True)
    usertag = Column(String,unique=True)
    password = Column(String(64))
    timejoined = Column(DateTime,index=True)
    messages_sent = Column(Integer(),default=0)
    last_seen = Column(DateTime,index=True)
    online = Column(Boolean)

class AccountSettings(Base):
    __tablename__ = 'account_personalisations'
    account = Column(Integer, ForeignKey('userlist.id'), primary_key=True)
    description = Column(String(256))
    time_changed = Column(DateTime)

class messagelist(Base):
    __tablename__ = 'messages'
    id = Column(Integer(),primary_key=True)
    content = Column(String(512),nullable=False)
    timesent = Column(DateTime)
    sender = Column(Integer,nullable=False)
    room = Column(Integer, nullable=False)
    
class messagelist_groups(Base):
    __tablename__ = 'messagesGroups'
    id = Column(Integer(),primary_key=True)
    content = Column(String(512),nullable=False)
    timesent = Column(DateTime)
    sender = Column(Integer,nullable=False)
    room = Column(Integer, nullable=False)
    isCommand = Column(Boolean)

class Friendship(Base):
    __tablename__ = 'friendships'
    id = Column(Integer,primary_key=True,autoincrement=True)
    user1 = Column(Integer)
    user2 = Column(Integer, ForeignKey('userlist.id'))
    friends_since = Column(DateTime)
    ended = Column(Boolean)
    lastMessage = Column(DateTime)

class Friend_Request(Base):
    __tablename__ = 'friend_requests'
    id = Column(Integer, primary_key=True)
    user1 = Column(Integer)
    user2 = Column(Integer, ForeignKey('userlist.id'))
    timesent = Column(DateTime)
    accepted = Column(Boolean,nullable=True)
    ended = Column(Boolean)

class Groups(Base):
    __tablename__ = 'groups'
    name = Column(String(30),unique=True)
    creator = Column(Integer, ForeignKey('userlist.id'))
    admin = Column(String)
    id = Column(Integer, primary_key=True)
    participants = Column(JSON)
    timecreated = Column(DateTime)
    lastMessage = Column(DateTime)
    
#Pydantic auth schemes:
class Token(BaseModel):
    access_token : str
    token_type : str
class Refresh_Token(BaseModel):
    refresh_token:str
    user:str
class Description(BaseModel):
    description:str
    username:str
class Config(BaseModel):
    authjwt_secret_key : str = '8870a9a3507f016b2a1f3489d182f1bba2360bee3ea5fe3b'