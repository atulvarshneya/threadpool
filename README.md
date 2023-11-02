# threadpool

class Future(job, runstatus, resultval, exception):
	job
		(fn, *args, **kwargs)
		fn is a callable object
	renstatus one of
		runstatus.INIT
		runstatus.RUNNING
		runstatus.COMPLETED 
	returnval
		the value returned by the job.
	exception
		any uncaught exception raised in the job.

	METHODS:
		done()
			RETURNS the current runstatus of the future
				runstatus.INIT
				runstatus.RUNNING
				runstatus.COMPLETED 

		wait()
			wait till future runstatus changes to runstatus.COMPLETED

		result()
			future's runstatus should be runstatus.COMPLETED for it to return a valid result.

			RAISES any uncaught exception raised during execution of the job.

			RETURNS the result.

	PROPERTIES
		job
		runstatus
		resultval
		exception



class Executor(nworkers)
	nworkers
		number of workers in the threadpool
		it can be used in a 'with clause' as -
		with threadpool.Executor(nworkers=10) as executor:
			results = map(fn, an_iterable)

	METHODS
		submit(fn, *args, **kwargs):
			submit a job as (fn, *args, **kwargs)
				fn is a callable object
			queues up the job to be executed by the threadpool workers

			RAISES a RuntimeExeption if executor is shutting down.

			RETURNS a future object for this job

		map(fn, iterable):
			fn is a callable object
			iterable is an object which is Iterable.
			map queues up execution of fn for each element of the iterable

			RAISES StopIteration when iterations over all futues is completed.
			RAISES any uncaught exception by any executions of fn.
			RAISES a RuntimeExeption if executor is shutting down.

			RETURNS an Iterable object which provides the results in the same order.

		wait_for_all()
			waits for all futures to complete execution.

		wait(future)
			wait for the given future to complete execution.

		shutdown()
			waits for all futures to complete, and then frees up all thread and queue resources.



class as_completed(futures_list)
	instantiates an Iterable object that wraps the provided list of futures.
	every call to next() on that Iterable object returns the next future that has completed execution.
	it waits till at least one future has reached runstatus.COMPLETED.
	the future_list is copied into a set internally so any duplicates are removed.

	METHODS
		next()
			RETURNS the next future that has runstatus as runstatus.COMPLETED.

			RAISES StopIteration when iterations over all futues is completed.
