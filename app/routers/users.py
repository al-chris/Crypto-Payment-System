# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from ..schemas import UserCreate, UserRead, Token
from ..crud import get_user_by_email, create_user
from ..models import User
from ..dependencies import get_session
from ..auth import hash_password, verify_password, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import os
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    tags=["users"],
)

@router.post("/register", response_model=UserRead)
async def register_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    existing_user = await get_user_by_email(session, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = hash_password(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_pwd
    )
    try:
        user_created = await create_user(session, new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="User registration failed")
    return user_created

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(session, email=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}