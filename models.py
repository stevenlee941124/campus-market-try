from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    products = relationship("Product", back_populates="owner")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    category = Column(String)
    description = Column(Text)
    image = Column(String)
    tags = Column(String)
    location = Column(String)
    contact_type = Column(String, default="other") # 新增：記錄是 IG、LINE 還是其他
    contact = Column(String) # 記錄 ID 或網址
    status = Column(String, default="上架中")
    created_at = Column(DateTime, default=datetime.now)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="products")

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# models.py 底部
class BarterSwipe(Base):
    __tablename__ = "barter_swipes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # 誰在滑
    target_product_id = Column(Integer, ForeignKey("products.id")) # 滑了哪件物品
    is_like = Column(Boolean) # True=右滑(喜歡), False=左滑(無感)
    created_at = Column(DateTime, default=datetime.now)

    # 建立關聯，方便後端直接讀取使用者資訊
    user = relationship("User")
    product = relationship("Product")