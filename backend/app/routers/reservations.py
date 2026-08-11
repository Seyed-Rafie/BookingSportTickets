from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import datetime
# فرض بر این است که تابع execute_query در فایل db/database.py قرار دارد
from app.db.database import execute_query 

router = APIRouter(prefix="/reservations", tags=["Reservations & Payments"])
