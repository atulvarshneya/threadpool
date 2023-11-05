
import threading

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

