
import threading
import queue
from .runstatus import Runstatus
from .future import Future

class Executor:

	def __init__(self, nworkers):
		self.threads = [threading.Thread(group=None, target=self.worker, name=f'thread{w}', args=(), kwargs={}, daemon=True) for w in range(nworkers)]
		self.futuresqueue = queue.Queue()
		self.poolON = True
		[t.start() for t in self.threads]

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, exception_traceback):
		self.shutdown()
		if exception_type is None:
			return True
		else:
			return False

	def submit(self, fn, *args, **kwargs):
		if not self.poolON:
			raise RuntimeError('Not allowed: Thread pool is shutting down.')
		job = (fn, args, kwargs)
		future = Future(job=job, runstatus=Runstatus.INIT, resultval=None, exception=None)
		self.futuresqueue.put(future)
		return future

	def map(self, fn, iterable):
		class results_cls:
			def __init__(self,futures):
				self.futures = futures
				self.index = 0
			def __iter__(self):
				return self
			def __next__(self):
				if self.index < len(self.futures):
					f = self.futures[self.index]
					self.index += 1
					f.wait()
				else:
					raise StopIteration
				return f.result()
		if not self.poolON:
			raise RuntimeError('Not allowed: Thread pool is shutting down.')
		futures = [self.submit(fn, i) for i in iterable]
		return results_cls(futures)

	def worker(self):
		while True:
			future = self.futuresqueue.get(block=True, timeout=None)
			job = future.job
			func = job[0]
			args = job[1]
			kwargs = job[2]
			try:
				future.runstatus = Runstatus.RUNNING
				retval = func(*args, **kwargs)
			except Exception as ex:
				future.exception = ex
				future.resultval = None
			else:
				future.resultval = retval
			future.runstatus = Runstatus.COMPLETED
			for cv in future.list_cvs():
				cv.acquire()
				cv.notify_all()
				cv.release()
			self.futuresqueue.task_done()

	def wait_for_all(self):
		# instead of waiting dor individual futures, we just wait for the queue to be emptied with all 'task_done()'
		self.futuresqueue.join()

	def wait(self, future):
		future.wait()

	def shutdown(self):
		# stop taking any further requests
		self.poolON = False

		# wait till all submits in queue are done (worker uses task_done() to report for each)
		self.futuresqueue.join()

		# free up all resources
		for t in self.threads:
			del(t)
		del(self.futuresqueue)

