import os
import time
from redis import Redis
from rq import Worker, Queue, Connection
from pipelines import load_into_images
from util import model_generate
from prometheus_metrics import OCR_JOBS_COMPLETED, OCR_JOBS_FAILED, OCR_PROCESSING_TIME, OCR_ACTIVE_JOBS

redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_conn = Redis.from_url(redis_url)
q = Queue('ocr', connection=redis_conn)

# Worker function used by the queue
def process_document_task(doc_id, path_on_disk, prompt):
    import json
    OCR_ACTIVE_JOBS.inc()
    start = time.time()
    try:
        with open(path_on_disk, 'rb') as f:
            data = f.read()
        images = load_into_images(data, path_on_disk)
        result = model_generate(images, prompt)

        # Save the result next to file or update DB (import inside to avoid circular)
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import Document, Base
        engine = create_engine('sqlite:///db.sqlite3')
        Session = sessionmaker(bind=engine)
        session = Session()
        doc = session.get(Document, doc_id)
        doc.result_json = result
        doc.status = 'done'
        doc.updated_at = datetime.utcnow()
        session.commit()

        OCR_JOBS_COMPLETED.inc()
    except Exception as e:
        OCR_JOBS_FAILED.inc()
        # update DB status to error
        raise
    finally:
        OCR_ACTIVE_JOBS.dec()
        OCR_PROCESSING_TIME.observe(time.time() - start)


if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(['ocr'])
        worker.work()