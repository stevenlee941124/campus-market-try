from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, database, auth_utils

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.post("/register")
def register(
    request: Request, # 新增 request 參數
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user_exists = db.query(models.User).filter(models.User.username == username).first()
    if user_exists:
        # 註冊失敗：回傳帶有 error 訊息的 HTML
        return templates.TemplateResponse("login.html", {"request": request, "error": "此帳號已被註冊！請換一個。"})
    
    hashed_password = auth_utils.get_password_hash(password)
    new_user = models.User(username=username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    
    # 註冊成功：回傳帶有 success 訊息的 HTML
    return templates.TemplateResponse("login.html", {"request": request, "success": "註冊成功！請直接登入。"})

@router.post("/login")
def login(
    request: Request, # 新增 request 參數
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth_utils.verify_password(password, user.password_hash):
        # 登入失敗：回傳帶有 error 訊息的 HTML
        return templates.TemplateResponse("login.html", {"request": request, "error": "帳號或密碼錯誤！"})

    access_token = auth_utils.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    res = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    res.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return res

@router.get("/logout")
def logout():
    res = RedirectResponse(url="/")
    res.delete_cookie("access_token")
    return res