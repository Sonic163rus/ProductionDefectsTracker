from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import datetime
from contextlib import asynccontextmanager

# Модели данных
class DefectCreate(BaseModel):
    qr_code: str
    defect_type: str
    sr_characteristic: bool
    operation: str
    shift: str

class DefectResponse(BaseModel):
    id: int
    qr_code: str
    defect_type: str
    sr_characteristic: bool
    operation: str
    shift: str
    timestamp: str

# Создание и инициализация БД
def init_db():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT NOT NULL,
            defect_type TEXT NOT NULL,
            sr_characteristic BOOLEAN NOT NULL,
            operation TEXT NOT NULL,
            shift TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    init_db()
    yield
    # Очистка при остановке (если нужна)

app = FastAPI(title="Defect Tracking System", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/defects", response_model=DefectResponse)
async def create_defect(defect: DefectCreate):
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO defects (qr_code, defect_type, sr_characteristic, operation, shift)
        VALUES (?, ?, ?, ?, ?)
    ''', (defect.qr_code, defect.defect_type, defect.sr_characteristic, defect.operation, defect.shift))
    
    defect_id = cursor.lastrowid
    conn.commit()
    
    # Получаем созданную запись
    cursor.execute('SELECT * FROM defects WHERE id = ?', (defect_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return DefectResponse(
            id=row[0],
            qr_code=row[1],
            defect_type=row[2],
            sr_characteristic=bool(row[3]),
            operation=row[4],
            shift=row[5],
            timestamp=row[6]
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to create defect")

@app.get("/api/defects", response_model=List[DefectResponse])
async def get_defects():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM defects ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    
    defects = []
    for row in rows:
        defects.append(DefectResponse(
            id=row[0],
            qr_code=row[1],
            defect_type=row[2],
            sr_characteristic=bool(row[3]),
            operation=row[4],
            shift=row[5],
            timestamp=row[6]
        ))
    
    return defects

@app.get("/")
async def root():
    return {"message": "Defect Tracking System API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
