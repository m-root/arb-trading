import time
import datetime
import queue
import threading

WORKER_TIMEOUT = 5.0


def batch_request_handler(rpc_request_queue, provider, response_processing_fn):
    '''  '''
    last_job = None
    while 1:
        try:
            if (datetime.datetime.utcnow() - last_job).total_seconds() > WORKER_TIMEOUT:
                response_processing_fn(('', '', 'TimeoutError'))
                break
            job = rpc_request_queue.get()
            if job is None:
                break
            last_job = datetime.datetime.utcnow()
            try:
                result = provider._make_request(job)
                response_processing_fn((job, result, ''))
            except Exception as exc:
                response_processing_fn((job, '', exc))
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            rpc_request_queue.task_done()
        time.sleep(0.1)


def batch_request(provider, payload, response_processing_fn, max_request_threads=10, max_request_q=200):
    '''
        could change provider to provider_type and then create provider in the worker to
        avoid any possible thread-safety issues now of down the road.
        also should take threading.Event, adjust worker while condition accordingly, so user can kill it all at will
   '''

    rpc_reqeuest_queue = queue.Queue()

    request_args = (rpc_reqeuest_queue, provider, response_processing_fn)
    req_threads = []

    for i in range(max_request_threads):
        t = threading.Thread(target=batch_request_handler, args=request_args)
        t.setDaemon(True)  # we don't really need it since we're joining but it helps to avoid zombies
        t.name = f'batch request thread {i}'
        req_threads.append(t)

    [t.start() for t in req_threads]

    for job in payload:
        rpc_reqeuest_queue.put(job)

    time.sleep(WORKER_TIMEOUT + 1.0)
    [t.join() for t in req_threads]


# user side
class SuperSimplClientBatchProcessingClass:
    def __init__(self, batch_size):
        ''' '''
        self.expected_results = batch_size
        self.jobs_processed = 0

    def job_update(self, data):
        ''' only requirement from web3py side is to be able to accept a (named) tuple '''
        self.jobs_processed += 1
        if data[1]:
            pass  # do something with successes
        else:
            pass  # do something with failures including TimeoutError

    @property
    def done(self):
        if len(self.jobs_processed) == self.jobs_processed:
            return True
        else:
            return False

    @property
    def progress(self):
        return {'batch-size': self.batch_size, 'processed_jobs': self.jobs_processed}