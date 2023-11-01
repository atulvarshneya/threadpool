import threading
from enum import Enum
import queue


class runstatus(Enum):
	INIT = 0
	RUNNING = 1
	COMPLETED = 2


class Future:
	def __init__(self, job, runstatus, resultval, exception):
		self.lock = threading.Lock()
		self.job = job
		self.runstatus = runstatus
		self.resultval = resultval
		self.exception = exception
		self.cvs = set()
		pass

	def __str__(self):
		return f'Future: job: {self.job}, runstatus: {self.runstatus}, resultval: {self.resultval}, exception: {self.exception}'

	def done(self):
		with self.lock:
			retval = True if self._runstatus == runstatus.COMPLETED else False
		return retval

	def add_cv(self, cv):
		if not isinstance(cv, threading.Condition):
			raise RuntimeError('ERROR: only threading.Condition expected as argument')
		with self.lock:
			self.cvs.add(cv)

	def rem_cv(self, cv):
		with self.lock:
			self.cvs.remove(cv)

	def list_cvs(self):
		with self.lock:
			retval = list(self.cvs)
		return retval

	def wait(self):
		if not self.done():
			cv = threading.Condition(lock=threading.Lock())
			self.add_cv(cv)
			cv.acquire()
			cv.wait()
			cv.release()
			self.rem_cv(cv)

	@property
	def job(self):
		with self.lock:
			retval = self._job
		return retval
	@job.setter
	def job(self, value):
		with self.lock:
			self._job = value

	@property
	def runstatus(self):
		with self.lock:
			retval = self._runstatus
		return retval
	@runstatus.setter
	def runstatus(self, value):
		with self.lock:
			self._runstatus = value

	@property
	def resultval(self):
		with self.lock:
			if self._exception is not None:
				raise self._exception
			retval = self._resultval
		return retval
	@resultval.setter
	def resultval(self, value):
		with self.lock:
			self._resultval = value
	def result(self):
		return self.resultval

	@property
	def exception(self):
		with self.lock:
			retval = self._exception
		return retval
	@exception.setter
	def exception(self, value):
		with self.lock:
			self._exception = value


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
		future = Future(job=job, runstatus=runstatus.INIT, resultval=None, exception=None)
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
				future.runstatus = runstatus.RUNNING
				retval = func(*args, **kwargs)
			except Exception as ex:
				future.exception = ex
				future.resultval = None
			else:
				future.resultval = retval
			future.runstatus = runstatus.COMPLETED
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

class as_completed:
	def __init__(self, futures_list):
		# check if a list or a dict
		flist = futures_list
		if isinstance(flist, dict):
			flist = list(flist.keys())
		if not isinstance(flist, list):
			raise RuntimeError('ERROR: expected list of futures, or dict with keys as futures.')

		# store as a set - thus avoiding dups, and creates a local copy of the list
		self.fset = set(flist)

		# add a [acquired] condition variable to all futures in this list
		self.cv = threading.Condition(lock=threading.Lock())
		[f.add_cv(self.cv) for f in self.fset]

	def __iter__(self):
		return self
	def __next__(self):
		if len(self.fset) < 1:
			raise StopIteration
		retval = None
		while True:
			for f in self.fset:
				if f.done():
					retval = f
					f.rem_cv(self.cv)
					self.fset.remove(f)
					break
			if retval == None:
				self.cv.acquire()
				self.cv.wait()
				self.cv.release()
			else:
				break
		return retval


if __name__ == '__main__':
	import time
	
	def func(a, b):
		sleeptime = a*2+1
		print(f'func({a}, {b}), sleeping for {sleeptime}...')
		time.sleep(sleeptime)
		print(f'func({a},{b}) DONE')

	executor = Executor(nworkers=3)

	futures = [executor.submit(func, i, b='param') for i in range(5)]

	executor.wait(futures[2])
	print('wait() for future 2 over')

	executor.shutdown()
