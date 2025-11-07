from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import sqlite3
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

# Модель данных
class DefectCreate(BaseModel):
    qr_code: str
    defect_type: str
    sr_characteristic: bool = False
    operation: str

# Инициализация базы данных
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
    init_db()
    yield

app = FastAPI(title="Defect Tracking System", lifespan=lifespan)

# Middleware для кодировки
@app.middleware("http")
async def add_charset_header(request: Request, call_next):
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Определение смены по времени
def get_shift():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 14:
        return "утро"
    elif 14 <= hour < 22:
        return "вечер"
    else:
        return "ночь"

# Эндпоинты
@app.get("/")
async def root():
    return {"message": "Defect Tracking System API"}

@app.post("/api/defects")
async def create_defect(defect: DefectCreate):
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    shift = get_shift()
    
    cursor.execute('''
        INSERT INTO defects (qr_code, defect_type, sr_characteristic, operation, shift)
        VALUES (?, ?, ?, ?, ?)
    ''', (defect.qr_code, defect.defect_type, defect.sr_characteristic, defect.operation, shift))
    
    conn.commit()
    defect_id = cursor.lastrowid
    conn.close()
    
    return {"id": defect_id, "message": "Defect recorded successfully"}

@app.get("/api/defects")
async def get_defects():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM defects ORDER BY timestamp DESC')
    defects = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "qr_code": row[1],
            "defect_type": row[2],
            "sr_characteristic": bool(row[3]),
            "operation": row[4],
            "shift": row[5],
            "timestamp": row[6]
        }
        for row in defects
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ДОБАВИТЬ В КОНЕЦ main.py:

@app.get("/api/stats/summary")
async def get_stats_summary():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    
    # Общее количество дефектов
    cursor.execute("SELECT COUNT(*) FROM defects")
    total = cursor.fetchone()[0]
    
    # Дефекты за сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM defects WHERE DATE(timestamp) = ?", (today,))
    today_count = cursor.fetchone()[0]
    
    # Критические дефекты
    cursor.execute("SELECT COUNT(*) FROM defects WHERE sr_characteristic = 1")
    critical = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_defects": total,
        "today_defects": today_count, 
        "critical_defects": critical,
        "defect_rate": round((today_count / 1000) * 100, 2)  # 1000 изделий в день
    }

@app.get("/api/stats/by-type")
async def get_stats_by_type():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT defect_type, COUNT(*) as count 
        FROM defects 
        GROUP BY defect_type 
        ORDER BY count DESC
    """)
    
    result = [{"type": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

@app.get("/api/stats/by-operation")
async def get_stats_by_operation():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT operation, COUNT(*) as count 
        FROM defects 
        GROUP BY operation 
        ORDER BY count DESC
    """)
    
    result = [{"operation": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

@app.get("/api/stats/by-shift")
async def get_stats_by_shift():
    conn = sqlite3.connect('defects.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT shift, COUNT(*) as count 
        FROM defects 
        GROUP BY shift 
        ORDER BY count DESC
    """)
    
    result = [{"shift": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return result

