# ЛР №3 (варіант 7): облік часу реагування на інциденти

Сервіс зберігає вимірювання часу реагування на інциденти.
Категорії: account, network, endpoint. `value` - хвилини (float >= 0),
поріг варіанта 30.0, `status` - new / in_progress / done.

## Встановлення
```bash
pip install -r requirements.txt
```

## Початкове заповнення (з кореня репозиторію)
```bash
python -m labs.lab03.seed
```

## Запуск API
```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs

## Приклади
```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=2&status=new&limit=5"
curl -i -X POST "http://127.0.0.1:8000/records" -H "Content-Type: application/json" \
  -d '{"code":"V07-TEST","title":"Тестове вимірювання","category_id":1,"value":15.5,"status":"new"}'
```