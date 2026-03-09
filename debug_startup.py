import traceback, sys
try:
    import app.main
except Exception as e:
    with open(r'e:\Stock Analysier and pedction machine\startup_error.txt', 'w') as f:
        traceback.print_exc(file=f)
    traceback.print_exc()
