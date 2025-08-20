import os
import uvicorn


def run_uvicorn():
    uvicorn.run('lenticularlens.api:app', host='0.0.0.0', port=8000, timeout_keep_alive=60,
                log_level=os.environ.get('LOG_LEVEL', 'INFO').lower())


if __name__ == "__main__":
    run_uvicorn()
