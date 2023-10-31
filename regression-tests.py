#!/usr/bin/env python

import time
import threadpool as tp


def func(a, b):
    sleeptime = a*2+1
    print(f'func({a}, {b}), sleeping for {sleeptime}...')
    time.sleep(sleeptime)
    print(f'func({a},{b}) DONE')


print('Test 01 -----------------------------------')
print("""Submit 5 jobs, 3 threads.
EXPECT: All jobs complete.
""")
executor = tp.Executor(nworkers=3)
futures = [executor.submit(func, i, b='param') for i in range(5)]
executor.shutdown()

print()
print('Using with clause.')
with tp.Executor(nworkers=3) as executor:
    futures = [executor.submit(func, i, b='param') for i in range(5)]

print('Done Test 01 ------------------------------')
print()


print('Test 02 -----------------------------------')
print("""Submit 5 jobs, 3 threads.
Wait for 3rd future (func 2) to complete.
EXPECT: Message about wait() over after func 2 DONE. Rest of all jobs complete after that.
""")
executor = tp.Executor(nworkers=3)
futures = [executor.submit(func, i, b='param') for i in range(5)]
executor.wait(futures[2])
print('wait() for future 2 over')
executor.shutdown()
print('Done Test 02 ------------------------------')
print()


print('Test 03 -----------------------------------')
print("""Submit 5 jobs, 3 threads.
Wait_for_all() to complete. Then use as_completed() to iterate through all futures.
EXPECT: Message about wait_for_all() over after all fun's DONE. All 5 as_complete() get done together after that.
""")
executor = tp.Executor(nworkers=3)
futures = [executor.submit(func, i, b='param') for i in range(5)]
executor.wait_for_all()
print('wait_for_all() over')
for f in tp.as_completed(futures):
    print(f'as_completd -- {f.job[0].__name__} {f.job[1]}, {f.job[2]}: f.done() = {f.done()}.  Check {f.list_cvs()}')
print('as_completed DONE')
executor.shutdown()
print('Done Test 03 ------------------------------')
print()


print('Test 04 -----------------------------------')
print("""Submit 5 jobs, 3 threads.
Wait() for future 3 (func 2) to complete. Then use as_completed() to iterate through all futures.
EXPECT: Message about wait() over after func 2 DONE. First 3 as_completed() reported immediately, other 2 track completion of func's.
""")
executor = tp.Executor(nworkers=3)
futures = [executor.submit(func, i, b='param') for i in range(5)]
executor.wait(futures[2])
print('wait() for future 2 over')
for f in tp.as_completed(futures):
    print(f'as_completd -- {f.job[0].__name__} {f.job[1]}, {f.job[2]}: f.done() = {f.done()}.  Check {f.list_cvs()}')
print('as_completed DONE')
executor.shutdown()
print('Done Test 04 ------------------------------')
print()


print('Test 05 -----------------------------------')
print("""Submit 5 jobs, 3 threads. Fetch results from all futures.
All jobs complete, except for func 2 raises an exception.
EXPECT: All futures return appropriate results, future 2 raises an exception.
""")
def func_exception(a, b):
    sleeptime = a
    time.sleep(sleeptime)
    if a == 2:
        print(f'func({a},{b}) DONE with EXCEPTION')
        raise Exception('Exception test')
    else:
        print(f'func({a},{b}) DONE')
    return sleeptime

with tp.Executor(nworkers=3) as executor:
    futures = [executor.submit(func_exception, i, b='param') for i in range(5)]

print()
print('fetching results from all futures')
for f in futures:
    try:
        print(f'{f.job[0].__name__} {f.result()}')
    except Exception as ex:
        print(ex)
print('Done Test 05 ------------------------------')
print()
