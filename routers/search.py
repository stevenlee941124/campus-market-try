from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, database

router = APIRouter(prefix="/search", tags=["search"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
def search_products(
    request: Request, 
    q: str = "", 
    min_p: float = 0, 
    max_p: float = 999999, 
    db: Session = Depends(database.get_db)
):
    # 先篩選價格區間
    query = db.query(models.Product).filter(
        models.Product.price >= min_p,
        models.Product.price <= max_p
    )
    
    # 如果有關鍵字，同時比對名稱與標籤
    if q:
        query = query.filter(
            (models.Product.name.contains(q)) | (models.Product.tags.contains(q))
        )
    
    products = query.all()
    return templates.TemplateResponse("category.html", {
        "request": request, 
        "products": products, 
        "current_category": f"搜尋結果: {q} (價格: {min_p}~{max_p})"
    })