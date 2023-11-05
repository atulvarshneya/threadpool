

from .executor import Executor
from .as_completed import as_completed


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
