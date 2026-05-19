from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from jose import jwt
import models, database, auth_utils

router = APIRouter(prefix="/barter", tags=["barter"])
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        return payload
    except: return None

# 1. 進入以物易物滑卡頁面
@router.get("/")
def barter_page(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    if not user: return templates.TemplateResponse("login.html", {"request": request, "error": "請先登入才能開始換物！"})
    
    user_id = user.get("user_id")
    
    # 演算法：篩選出「我沒滑過」且「不是我的」商品，隨機排序
    swiped_ids = db.query(models.BarterSwipe.target_product_id).filter(models.BarterSwipe.user_id == user_id).all()
    swiped_ids = [i[0] for i in swiped_ids]
    
    available_products = db.query(models.Product).filter(
        models.Product.owner_id != user_id,
        models.Product.id.notin_(swiped_ids)
    ).order_by(func.random()).limit(10).all()

    return templates.TemplateResponse("barter.html", {"request": request, "products": available_products, "user": user})

# 2. 處理滑動動作 (API)
@router.post("/swipe/{product_id}")
async def handle_swipe(product_id: int, is_like: bool, request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    if not user: return JSONResponse(status_code=401, content={"msg": "未登入"})
    
    my_id = user.get("user_id")
    
    # 記錄這筆滑動
    swipe = models.BarterSwipe(user_id=my_id, target_product_id=product_id, is_like=is_like)
    db.add(swipe)
    db.commit()

    # 如果是右滑，判斷是否 Match
    if is_like:
        target_product = db.query(models.Product).filter(models.Product.id == product_id).first()
        target_owner_id = target_product.owner_id
        
        # 關鍵配對邏輯：對方是否也右滑過「我的」任何一個商品？
        match = db.query(models.BarterSwipe).join(models.Product, models.BarterSwipe.target_product_id == models.Product.id)\
                  .filter(models.BarterSwipe.user_id == target_owner_id)\
                  .filter(models.BarterSwipe.is_like == True)\
                  .filter(models.Product.owner_id == my_id).first()
        
        if match:
            return {"status": "match", "target_name": target_product.name, "contact": target_product.contact}

    return {"status": "ok"}

@router.get("/matches")
def get_matches(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/login")
    
    my_id = user.get("user_id")
    
    # 核心邏輯：找出雙向喜歡的配對
    # 1. 找出我右滑(Like)過的所有紀錄
    my_likes = db.query(models.BarterSwipe).filter(
        models.BarterSwipe.user_id == my_id,
        models.BarterSwipe.is_like == True
    ).all()
    
    matches = []
    for swipe in my_likes:
        their_product = swipe.product
        their_id = their_product.owner_id
        
        # 2. 檢查這位「對方主人」是否也右滑過「我的」任何一件商品
        partner_like = db.query(models.BarterSwipe).join(models.Product).filter(
            models.BarterSwipe.user_id == their_id,
            models.BarterSwipe.is_like == True,
            models.Product.owner_id == my_id
        ).first()
        
        if partner_like:
            # 如果對方也喜歡我的某件物品，這就是一個 Match！
            matches.append({
                "their_item": their_product,
                "my_item": partner_like.product, # 對方喜歡我的哪件東西
                "partner_name": their_product.owner.username,
                "contact_type": their_product.contact_type,
                "contact": their_product.contact
            })
            
    return templates.TemplateResponse("matches.html", {
        "request": request, 
        "matches": matches, 
        "user": user
    })

# 找到 routers/barter.py 並加入以下路由

# routers/barter.py

@router.post("/unmatch/{product_id}")
def unmatch_product(product_id: int, request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    if not user:
        return {"status": "error", "message": "未登入"}
    
    my_id = user.get("user_id")
    
    # 刪除「我右滑對方物品」的紀錄
    swipe_record = db.query(models.BarterSwipe).filter(
        models.BarterSwipe.user_id == my_id,
        models.BarterSwipe.target_product_id == product_id,
        models.BarterSwipe.is_like == True
    ).first()
    
    if swipe_record:
        db.delete(swipe_record)
        db.commit()
        return {"status": "ok"}
    
    return {"status": "error", "message": "找不到配對紀錄"}