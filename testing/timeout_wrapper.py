import threading
import sys
from functools import wraps

# Global timeout tracker
_timeout_occurred = False


def timeout(seconds: int = 60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                global _timeout_occurred
                _timeout_occurred = True
                print(f"Warning: Function '{func.__name__}' timed out after {seconds} seconds")
                return None
            
            if exception[0] is not None:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator


def check_timeouts_and_exit():
    """Check if any timeouts occurred and exit with code 1 if so"""
    global _timeout_occurred
    if _timeout_occurred:
        print("Exiting with code 1 due to timeout(s)")
        sys.exit(1)


if __name__ == "__main__":
    import time
    
    @timeout(3)
    def fast_function():
        time.sleep(2)
        return "Completed"
    
    @timeout(3)
    def slow_function():
        time.sleep(5)
        return "Completed"
    
    print("Testing timeout decorator...")
    
    print(f"Fast: {fast_function()}")
    print(f"Slow: {slow_function()}")
    print("Program continues after timeouts!")
    
    # Check if any timeouts occurred and exit with code 1 if so
    check_timeouts_and_exit()

