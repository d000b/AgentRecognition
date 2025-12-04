from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Counters and gauges
OCR_JOBS_CREATED = Counter('ocr_jobs_created_total', 'Total OCR jobs created')
OCR_JOBS_COMPLETED = Counter('ocr_jobs_completed_total', 'Total OCR jobs completed')
OCR_JOBS_FAILED = Counter('ocr_jobs_failed_total', 'Total OCR jobs failed')
OCR_ACTIVE_JOBS = Gauge('ocr_active_jobs', 'Active OCR jobs in processing')
OCR_PROCESSING_TIME = Histogram('ocr_processing_seconds', 'OCR processing time in seconds')


def metrics_response():
    return generate_latest()
