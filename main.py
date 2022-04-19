from array import array
from operator import and_, or_,__contains__
from typing import List
from fastapi import FastAPI, Request,Depends
from fastapi.staticfiles import StaticFiles
from database import *
from pydantic import BaseModel, Json
from starlette.requests import Request
from datetime import datetime
from auth import *
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
#app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
)
class user(BaseModel):
    username:str
    password:str
class RegisterData(BaseModel):
    email:str
    username:str
    password:str
class message(BaseModel):
    content:str
    sender:str
    room:int
    type:bool
class friendrequest_answer(BaseModel):
    username:str
    answer:bool
    user2:str
class friendrequestRemove(BaseModel):
    usr_from:str
    usr_to:str
class friendrequest(BaseModel):
    usr_from:str
    usr_to:str
    areFriends:bool
    method:bool
class name_fragment(BaseModel):
    username_fragment:str
class room_send(BaseModel):
    room:int
    isgroup:bool
class friendCheck(BaseModel):
    current_user:str
    username:str
class group(BaseModel):
    groupName: str
    userCreator: str
    groupMembers: List[str]
class get_groups(BaseModel):
    username:str
class unfriend(BaseModel):
    username:str
    friend:str
@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
#Endpoints:
@app.post('/get_msg')
async def get_msg(room:room_send):
    with Session(engine) as db:
        if room.isgroup:
            msgs = db.execute('SELECT * FROM messagesGroups WHERE room = :roomId',{'roomId':room.room})
            msg_array = []
            for msg in msgs:
                msg_array.append(msg)
            return{"messages":msg_array}
        elif  room.isgroup is not True:
            msgs = db.execute('SELECT * FROM messages WHERE room = :roomId',{'roomId':room.room})
            msg_array = []
            for msg in msgs:
                msg_array.append(msg)
            return{"messages":msg_array}
    return{'code':'error'}
@app.post('/send_msg')
async def send_msg(message:message):
    time_sent = datetime.now()
    if message.type:
        append_msg = messagelist_groups(content=message.content,timesent=time_sent,sender=message.sender,room=message.room)
    elif message.type is False:
        append_msg = messagelist(content=message.content,timesent=time_sent,sender=message.sender,room=message.room)
    user = get_user(message.sender)
    with Session(engine) as db:
        db.execute('UPDATE userlist SET messages_sent = :msgs WHERE username = :val',{'val':message.sender,'msgs':user.messages_sent+1})
        db.add(append_msg)
        db.commit()
        if message.type:
            messages = db.query(messagelist_groups).filter(messagelist_groups.timesent == time_sent).first()
            db.execute('UPDATE groups SET lastMessage = :timevar WHERE id = :room',{'timevar':time_sent,'room':message.room})

        elif message.type is False:
            messages = db.query(messagelist).filter(messagelist.timesent == time_sent).first()
            db.execute('UPDATE friendships SET lastMessage = :timevar WHERE id = :room',{'timevar':time_sent,'room':message.room})
        db.commit()
        if messages is not None:
            return{'id':messages.id, 'content': message.content,'timesent':time_sent,'sender': messages.sender,'room': messages.room,'type':message.type}
@app.post('/query_users')
async def query_users(username_fragment:name_fragment):
    with Session(engine) as db:
        try:
            fragment_try = db.execute('SELECT * FROM userlist WHERE username like :userfragment',{'userfragment':f'{username_fragment.username_fragment}%'})
            user_fragment_array = []
            for row in fragment_try:
                user_fragment_array.append(row['username'])
        except Exception as e:
            print(e)
            db.rollback()
        finally:
            return{"found_users":user_fragment_array}
    
@app.post('/login')
async def login_user(userdata:user,Authorize:AuthJWT = Depends()):
    user = get_user(userdata.username)
    if user is not False:
        if password_verify(userdata.password,user.password):
            user.last_seen = datetime.now()
            access_token = Authorize.create_refresh_token(subject=user.username)
            return{'code':'success','token':access_token}
    return{'code':'error'}
@app.post('/refresh_token_renew')
async def token_renew(token:Refresh_Token,Authorize: AuthJWT = Depends()):
    if token.user != '':
        try:
            access_token = Authorize.create_refresh_token(subject=token.user)
            user = token.user
            return{'code':'success','token':access_token,'user':user}
        except:
            return{'code':'error'}
    return{'code':'error'}
@app.post('/users/{username}')
async def user_profile_get(username:str):
    user = get_user(username)
    if user is not False:
        return {'username':user.username}
    return{'username':'not_found'}
@app.post('/users/description_set/{username}')
async def user_profile_description_set(data:Description):
    user = get_user(data.username)
    if user is not False:
        with Session(engine) as db:
            db.execute('UPDATE account_personalisations SET description = :descript WHERE account = :account',{'account':user.username,'descript':data.description})
            db.commit()
        return {'status':'success','username':user.username,'description':data.description}
    return{'status':'error'}
@app.get('/users/description_get/{username}')
async def description_get(username):
    user = get_user(username)
    if user is not False:
        with Session(engine) as db:
            description = db.query(AccountSettings).filter(AccountSettings.account == user.id).first()
            if description is not None:
                return{'status':'success','description':description.description}
            return{'status':'success','description':''}
    return{'status':'no such user..'}
@app.post("/sign-up")
async def signup(data:RegisterData,Authorize:AuthJWT = Depends()):
    if credential_check(data.username,data.email):
        new_user_assignment(data.email,data.username,data.password)
        access_token = Authorize.create_refresh_token(subject=data.username)
        return{'code':'success','token':access_token}
    return{'code':'error'}
@app.post('/is_online/{user}')
async def is_online(user):
    user = get_user(user)
    if user is not False:
        with Session(engine) as db:
            db.execute('UPDATE userlist SET last_seen = :timer, online = :onlinevar WHERE username = :val',{'val':user.username,'timer':datetime.now(),'onlinevar':True})
            db.commit()
        return{}
@app.post('/check_online_status/{username}')
async def check_online_status(data:friendCheck):
    user = get_user(data.username)
    with Session(engine) as db:
        arefriends = db.execute('SELECT * FROM friendships WHERE user1 = :usr1 AND user2 = :usr2 OR user2 = :usr1 AND user1 = :usr2',{'usr1':data.username,'usr2':data.current_user})
        friends = False
        requestPresent = False
        isFromMe = False
        present = db.query(Friend_Request).filter(or_(and_(Friend_Request.user1 == data.username, Friend_Request.user2 == data.current_user),and_(Friend_Request.user2 == data.username, Friend_Request.user1 == data.current_user))).first()
        if present is not None:
            requestPresent = True
            if present.user1 == data.current_user:
                isFromMe = True
        for friend in arefriends:
            if friend.user1 == data.current_user and friend.ended == False or  friend.user2 == data.current_user and friend.ended == False:
                friends = True
    if user is not False:
        return{'isOnline':user.online,'lastSeen':user.last_seen,'areFriends':friends,'isPresent':requestPresent,'isFromMe':isFromMe}
    return{'code':'error'}
@app.post('/last_seen/{username}')
async def last_seen(username):
    user = get_user(username)
    if user is not False:
        return{'last_seen':user.last_seen}
@app.post('/set_offline/{username}')
async def set_offline(username): 
    with Session(engine) as db:
            db.execute('UPDATE userlist SET last_seen = :timer, online = :onlinevar WHERE username = :val',{'val':username,'timer':datetime.now(),'onlinevar':False})
            db.commit()
@app.post('/send_friend_req/{usr_from}')
async def send_friend_req(data:friendrequest): 
    with Session(engine) as db:
        if data.areFriends == False:
            if data.method == True:  
                friend_req = Friend_Request(user1 = data.usr_from,user2 = data.usr_to,timesent=datetime.now(),accepted=False,ended=False)
                db.add(friend_req)
                db.commit()
                return{'areFriends':True,'isPresent':True}
            elif data.method == False:
                db.execute('DELETE FROM friend_requests WHERE user1 = :usr1 AND user2 = :usr2 OR user2 = :usr1 AND user1 = :usr2',{'usr1':data.usr_from,'usr2':data.usr_to})
                db.commit()
                return{'areFriends':False,'isPresent':False}
        elif data.areFriends == True:
            if data.method == True:
                db.execute('UPDATE friendships SET ended = :val WHERE user1 = :usr1 AND user2 = :usr2 OR user2 = :usr1 AND user1 = :usr2',{'usr1':data.usr_from,'usr2':data.usr_to,'val':True})
                db.commit()
                return{'areFriends':False,'isPresent':False}
    return {'code':'error'}
@app.post('/get_friend_req/{username}')
async def get_friend_req(username):
    with Session(engine) as db:
        found_friend_requests = db.execute('SELECT * FROM friend_requests WHERE ended = :ended AND user2 = :user',{'user':username,'ended':False})
        friend_request_array = []
        for friend_request in found_friend_requests:
            friend_request_array.append(friend_request)
        return{'friend_requests':friend_request_array}
@app.post('/answer_friend_req/{username}')
async def answer_frined_req(data:friendrequest_answer):
    with Session(engine) as db:
        db.execute('UPDATE friend_requests SET accepted = :answer, ended = :ended WHERE user1 =:usr1 AND user2 = :usr2 OR user1 =:usr2 AND user2 = :usr1',{'usr1':data.username,'usr2':data.user2,'answer':data.answer,'ended':True})
        if data.answer is True:
            werefriends = db.query(Friendship).filter(or_(and_(Friendship.user1 == data.username, Friendship.user2 == data.user2),(and_(Friendship.user2 == data.username, Friendship.user1 == data.user2)))).first()
            if werefriends is None or werefriends is null:
                new_friends = Friendship(user1=data.username,user2=data.user2,friends_since=datetime.now(),ended=False)
                db.add(new_friends)
            else:
                db.execute('UPDATE friendships SET ended = :ended AND friends_since = :since WHERE user1 = :user1 AND user2 = :user2 OR user2 = :user1 AND user1 = :user2',{'user1':data.username,'user2':data.user2,'ended':False,'since':datetime.now()})
        db.execute('DELETE FROM friend_requests WHERE user1 = :usr1 AND user2 = :usr2 OR user2 = :usr1 AND user1 = :usr2',{'usr1':data.username,'usr2':data.user2})
        db.commit()
    return{}
@app.post('/get_friendlist/{username}')
async def get_friendlist(username):
    with Session(engine) as db:
        users_array = []
        users = db.execute('SELECT * FROM Friendships WHERE user1 = :USR OR user2 = :USR',{'USR':username})
        for user in users:
            if not user.ended:
                friend = ''
                if user.user1 == username:
                    friend = db.query(User).filter(User.username == user.user2).first()
                else:
                    friend = db.query(User).filter(User.username == user.user1).first()
                friendship = {'id':user.id,'friend':friend.username,'since':user.friends_since,'last_seen':friend.last_seen,'isonline':friend.online,'lastMessage':user.lastMessage}
                users_array.append(friendship)
            else:
                pass
        return{'friends':users_array}
@app.post('/create_group/{userCreator}')
async def create_group(data:group):
    user = get_user(data.userCreator)
    if user is not False:
        with Session(engine) as db:
            alreadyExists = db.query(Groups).filter(Groups.name == data.groupName).first()
            if alreadyExists is None or alreadyExists is null:
                new_group = Groups(name=data.groupName,creator=data.userCreator,participants=data.groupMembers,timecreated=datetime.now())
                db.add(new_group)
                db.commit()
                return{'code':'success'}
            else:
                return{'code':'Group already exists..'}
    return{'code':'error'}
@app.post('/get_groups/{username}')
async def get_groups_func(data:get_groups):
    user = get_user(data.username)
    if user is not None:
        with Session(engine) as db:
            groups = db.query(Groups).filter(Groups.participants.contains(data.username))
            groups_array = []
            for group in groups:
                groups_array.append(group)
            return{'groups':groups_array}
    return{'code':'error'}
@app.post('/unfriend/{username}')
async def unfriend(data:unfriend):
    user = get_user(data.username)
    if user is not False:
        with Session(engine) as db:
            db.execute('UPDATE friendships SET ended = :ended WHERE user1 = :user1 AND user2 = :user2 OR user2 = :user1 AND user1 = :user2',{'user1':data.username,'user2':data.friend,'ended':True})
            db.commit()
        return{'code':'success'}
    return{'code':'error'}
#Db start:
if not Base.metadata.create_all(bind=engine):
    Base.metadata.create_all(bind=engine)