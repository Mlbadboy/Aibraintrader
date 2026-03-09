import time
print('Line 1: import pandas as pd')
start = time.time()
import pandas as pd
print(f'Done ({time.time()-start:.2f}s)')

print('Line 2: from datetime import datetime')
start = time.time()
from datetime import datetime
print(f'Done ({time.time()-start:.2f}s)')

print('Line 3: import logging')
start = time.time()
import logging
print(f'Done ({time.time()-start:.2f}s)')
