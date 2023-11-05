
import threading
from .runstatus import Runstatus

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
			retval = True if self._runstatus == Runstatus.COMPLETED else False
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

	def result(self):
		if not self.done():
			cv = threading.Condition(lock=threading.Lock())
			self.add_cv(cv)
			cv.acquire()
			cv.wait()
			cv.release()
			self.rem_cv(cv)
		return self.resultval

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

	@property
	def exception(self):
		with self.lock:
			retval = self._exception
		return retval
	@exception.setter
	def exception(self, value):
		with self.lock:
			self._exception = value

