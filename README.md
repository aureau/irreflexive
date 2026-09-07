need python3.11+

## quick frontend setup
- cd into frontend
- npm install
- npm run dev

## quick backend setup
u can cd into backend or run from root
- python3 -m venv backend/.venv
- source backend/.venv/bin/activate
- pip install -r /backend/requirements.txt
- uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
