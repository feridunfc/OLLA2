import os, sys, uvicorn
sys.path.insert(0, '/app')
from fastapi import FastAPI
from multiai.core.metrics import get_metrics
app = FastAPI(title='OLLA2', version='5.2.0')
@app.get('/healthz')
def health(): return {'status': 'healthy', 'version': '5.2.0'}
@app.get('/metrics')
def metrics(): return get_metrics()
if __name__ == '__main__':
    uvicorn.run('entrypoint:app', host='0.0.0.0', port=8000, reload=False)
