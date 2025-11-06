import re

with open('main.py', 'r') as f:
    content = f.read()

# Проверяем наличие импортов
if 'from pydantic import BaseModel' not in content:
    # Находим место для вставки импортов (после существующих импортов)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('from') or line.startswith('import'):
            continue
        else:
            # Вставляем импорты перед первой не-импорт строкой
            lines.insert(i, 'from pydantic import BaseModel')
            break
    
    content = '\n'.join(lines)

with open('main.py', 'w') as f:
    f.write(content)

print("Импорты исправлены")
