import shutil
import os
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt
import models, database, auth_utils

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        return payload
    except: return None

# --- 路由開始 ---

@router.get("/")
def get_products(request: Request, category: str = None, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    products = db.query(models.Product).filter(models.Product.category == category).all() if category else db.query(models.Product).all()
    return templates.TemplateResponse("category.html", {"request": request, "products": products, "current_category": category or "全部", "user": user})

@router.get("/{product_id}")
def get_product_detail(request: Request, product_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    return templates.TemplateResponse("detail.html", {"request": request, "product": product, "user": user})

@router.post("/")
async def create_product(
    request: Request,
    name: str = Form(...), price: float = Form(...), category: str = Form(...),
    tags: str = Form(""), location: str = Form(...), contact_type: str = Form(...),
    contact: str = Form(...), description: str = Form(""),
    file: UploadFile = File(...), db: Session = Depends(database.get_db)
):
    user = get_current_user(request)
    user_id = user.get("user_id") if user else None
    
    os.makedirs("static/uploads", exist_ok=True)
    file_location = f"static/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    new_product = models.Product(
        name=name, price=price, category=category, tags=tags, location=location,
        contact_type=contact_type, contact=contact, description=description, 
        image=f"/static/uploads/{file.filename}", owner_id=user_id
    )
    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/seller/dashboard", status_code=303)

@router.get("/{product_id}/edit")
def edit_product_page(request: Request, product_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not user or not product or product.owner_id != user.get("user_id"):
        raise HTTPException(status_code=403, detail="權限不足")
    return templates.TemplateResponse("edit.html", {"request": request, "product": product, "user": user})

# 修正後的更新路由：確保所有聯絡資訊都有被接收並儲存
@router.post("/{product_id}/edit")
async def update_product(
    request: Request, product_id: int,
    name: str = Form(...), price: float = Form(...), category: str = Form(...),
    tags: str = Form(""), location: str = Form(...), 
    contact_type: str = Form(...), # 確保有這行
    contact: str = Form(...),      # 確保有這行
    description: str = Form(""),
    file: UploadFile = File(None), db: Session = Depends(database.get_db)
):
    user = get_current_user(request)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not user or not product or product.owner_id != user.get("user_id"):
        raise HTTPException(status_code=403, detail="權限不足")

    # 更新所有欄位
    product.name = name
    product.price = price
    product.category = category
    product.location = location
    product.tags = tags
    product.description = description
    product.contact_type = contact_type # 更新聯絡類型
    product.contact = contact           # 更新聯絡資訊

    if file and file.filename:
        file_location = f"static/uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        product.image = f"/static/uploads/{file.filename}"

    db.commit()
    return RedirectResponse(url="/seller/dashboard", status_code=303)

@router.post("/{product_id}/delete")
def delete_product(request: Request, product_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user(request)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not user or not product or product.owner_id != user.get("user_id"):
        raise HTTPException(status_code=403, detail="權限不足")
    db.delete(product)
    db.commit()
    return RedirectResponse(url="/seller/dashboard", status_code=303)