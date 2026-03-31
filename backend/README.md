# #алкардио API

## Тесты

```bash
cd backend
pip3 install -r requirements-test.txt
python3 -m pytest tests/ -v
```

Тестовая база: `test_starthub.db` (создаётся в каталоге `backend/`, основная `starthub.db` не используется при `STARTHUB_TESTING=1`).
