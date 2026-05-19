from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from routers import products, search, feedback, seller, auth
import models, database, auth_utils
from jose import jwt
from fastapi.responses import RedirectResponse
from routers import products, search, feedback, seller, auth, barter # 新增 barter

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="中興大學校園二手交易平台")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(products.router)
app.include_router(search.router)
app.include_router(feedback.router)
app.include_router(seller.router)
app.include_router(auth.router)
app.include_router(barter.router)

def get_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        return payload
    except:
        return None

@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    user = get_user_from_cookie(request)
    recent_products = db.query(models.Product).order_by(models.Product.id.desc()).limit(6).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "products": recent_products,
        "user": user
    })

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/post")
def post_page(request: Request):
    user = get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("post.html", {"request": request, "user": user})

@app.get("/contact")
def contact_page(request: Request):
    user = get_user_from_cookie(request)
    return templates.TemplateResponse("contact.html", {"request": request, "user": user})