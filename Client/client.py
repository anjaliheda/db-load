import requests
import time
import threading
import random
import statistics
from datetime import datetime
from collections import defaultdict

# Configuration
SINGLE_SERVER_URL = "http://server1:5000/request"
LOAD_BALANCER_URL = "http://loadbalancer:5000/request"
SET_ALGO_URL = "http://loadbalancer:5000/set_algorithm"

class PerformanceMetrics:
    """Track and analyze request performance metrics"""
    def __init__(self):
        self.response_times = []
        self.failed_requests = []  # Store failed request details
        self.total_requests = 0
        self.server_distribution = defaultdict(list)  # Store response times per server
        self.task_distribution = defaultdict(list)    # Store response times per task type
        self.start_time = None
        self.end_time = None
        self.error_distribution = defaultdict(int)    # Count different types of errors

    def record_request(self, server, task_type, response_time=None, error=None):
        """Record metrics for a single request"""
        if not self.start_time:
            self.start_time = datetime.now()
        
        self.total_requests += 1
        
        if response_time is not None:
            self.response_times.append(response_time)
            self.server_distribution[server].append(response_time)
            self.task_distribution[task_type].append(response_time)
        else:
            self.failed_requests.append({
                'server': server,
                'task_type': task_type,
                'error': error
            })
            self.error_distribution[str(error)] += 1
            
        self.end_time = datetime.now()

    def get_server_stats(self, server):
        """Calculate statistics for a specific server"""
        times = self.server_distribution[server]
        if not times:
            return None
        return {
            'count': len(times),
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0
        }

    def print_summary(self, phase_name):
        """Print comprehensive performance summary"""
        print(f"\n{'='*20} {phase_name} Summary {'='*20}")
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"Total Duration: {duration:.2f}s")
        print(f"Requests per second: {self.total_requests/duration:.1f}")

        print(f"\nRequest Statistics:")
        print(f"  Total Requests: {self.total_requests}")
        print(f"  Successful: {len(self.response_times)}")
        print(f"  Failed: {len(self.failed_requests)}")
        success_rate = (len(self.response_times)/self.total_requests*100)
        print(f"  Success Rate: {success_rate:.1f}%")

        if self.response_times:
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {statistics.mean(self.response_times):.2f}s")
            print(f"  Median: {statistics.median(self.response_times):.2f}s")
            print(f"  Min: {min(self.response_times):.2f}s")
            print(f"  Max: {max(self.response_times):.2f}s")
            if len(self.response_times) > 1:
                print(f"  Std Dev: {statistics.stdev(self.response_times):.2f}s")

        if self.server_distribution:
            print(f"\nServer Distribution and Performance:")
            total_successful = len(self.response_times)
            for server in sorted(self.server_distribution.keys()):
                stats = self.get_server_stats(server)
                request_count = len(self.server_distribution[server])
                percentage = (request_count/total_successful*100)
                print(f"  {server}:")
                print(f"    Requests: {request_count} ({percentage:.1f}%)")
                print(f"    Avg Response: {stats['avg']:.2f}s")
                print(f"    Min/Max: {stats['min']:.2f}s / {stats['max']:.2f}s")

        if self.task_distribution:
            print(f"\nTask Type Performance:")
            for task_type, times in sorted(self.task_distribution.items()):
                print(f"  {task_type:15s}: {len(times):3d} requests, "
                      f"avg={statistics.mean(times):.2f}s, "
                      f"max={max(times):.2f}s")

        if self.error_distribution:
            print(f"\nError Distribution:")
            for error, count in self.error_distribution.items():
                print(f"  {error}: {count} occurrences")

        print("=" * 60)

def generate_task():
    """Generate a random task with controlled distribution"""
    tasks = [
        # Light tasks (30% probability)
        *([{
            "task_type": "addition",
            "num1": random.randint(1, 100),
            "num2": random.randint(1, 100)
        }] * 15),
        *([{
            "task_type": "string_length",
            "text": "Hello" * random.randint(1, 10)
        }] * 15),
        
        # Medium tasks (40% probability)
        *([{
            "task_type": "multiplication",
            "num1": random.randint(1, 100),
            "num2": random.randint(1, 100)
        }] * 20),
        *([{
            "task_type": "find_vowels",
            "text": "Hello World" * random.randint(1, 5)
        }] * 20),
        
        # Heavy tasks (30% probability)
        *([{
            "task_type": "factorial",
            "num": random.randint(1, 7)
        }] * 15),
        *([{
            "task_type": "sort_large_list",
            "numbers": [random.randint(1, 1000) for _ in range(100)]
        }] * 15)
    ]
    return random.choice(tasks)

def send_request(url, metrics, task_id, batch_start_time=None):
    """Send a single request and record metrics"""
    task = generate_task()
    start_time = time.time()
    
    try:
        response = requests.post(url, json=task, timeout=30)
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            server = response.json().get('server', 'unknown')
            load = response.json().get('load', 'N/A')
            processing_time = response.json().get('processing_time', 'N/A')
            
            # Calculate queue time (time spent waiting before processing)
            queue_time = response_time - (processing_time if isinstance(processing_time, (int, float)) else 0)
            
            print(f"Request {task_id:3d} | {task['task_type']:15s} | "
                  f"Server: {server:15s} | Load: {load:2} | "
                  f"Time: {response_time:.2f}s (Queue: {queue_time:.2f}s)")
            
            metrics.record_request(server, task['task_type'], response_time)
        else:
            error_msg = f"Status {response.status_code}"
            if response.status_code == 503:
                error_msg = "Server Overloaded"
            print(f"Request {task_id:3d} | {task['task_type']:15s} | Failed: {error_msg}")
            metrics.record_request(None, task['task_type'], None, error_msg)
            
    except Exception as e:
        print(f"Request {task_id:3d} | {task['task_type']:15s} | Error: {str(e)}")
        metrics.record_request(None, task['task_type'], None, str(e))

def run_test_phase(url, num_requests, phase_name, delay_between_requests=0.1):
    """Run a test phase with the specified number of requests"""
    metrics = PerformanceMetrics()
    
    print(f"\n{'='*20} {phase_name} {'='*20}")
    print(f"Starting {num_requests} requests...")
    print("\nRequest ID | Task Type       | Server          | Load | Time (Queue)")
    print("-" * 75)
    
    # Create and start threads
    threads = []
    batch_start_time = time.time()
    
    for i in range(num_requests):
        thread = threading.Thread(
            target=send_request,
            args=(url, metrics, i+1, batch_start_time)
        )
        threads.append(thread)
        thread.start()
        time.sleep(delay_between_requests)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
        
    metrics.print_summary(phase_name)
    return metrics

def main():
    """Main test execution function"""
    # Test configuration
    NUM_REQUESTS = 100  
    DELAY_BETWEEN = 0.05  # Smaller delay to increase server stress
    
    print("\n=== Load Balancing Demonstration ===")
    print("This test will demonstrate the effectiveness of different load balancing strategies")
    
    # Phase 1: Single Server (to demonstrate overload)
    print("\nPhase 1: No Load Balancing (Single Server)")
    print("Sending all requests to a single server to demonstrate overload")
    single_metrics = run_test_phase(
        SINGLE_SERVER_URL, 
        NUM_REQUESTS, 
        "Single Server",
        DELAY_BETWEEN
    )
    
    time.sleep(5)  # Cool down period
    
    # Phase 2: Load Balanced Testing
    print("\nPhase 2: Load Balancing")
    print("Testing different load balancing algorithms")
    
    algorithms = ["round_robin", "source_hashing", "least_loaded"]
    algorithm_metrics = {}
    
    for algorithm in algorithms:
        print(f"\nConfiguring load balancer to use {algorithm} algorithm...")
        try:
            response = requests.post(SET_ALGO_URL, json={"algorithm": algorithm})
            if response.status_code == 200:
                print(f"Successfully set algorithm to {algorithm}")
            else:
                print(f"Failed to set algorithm: {response.status_code}")
                continue
        except Exception as e:
            print(f"Error setting algorithm: {str(e)}")
            continue
            
        time.sleep(3)  
        
        algorithm_metrics[algorithm] = run_test_phase(
            LOAD_BALANCER_URL, 
            NUM_REQUESTS, 
            f"Load Balanced ({algorithm})",
            DELAY_BETWEEN
        )
        time.sleep(3)  # Cool down between algorithms
    
    # Final comparison
    print("\n=== Final Comparison ===")
    print("\nMetric          | Single Server | Round Robin  | Source Hash  | Least Loaded")
    print("-" * 75)
    
    def get_stats(metrics):
        if not metrics or not metrics.response_times:
            return "N/A", "N/A", "N/A", "N/A", "N/A"
        return (
            f"{(len(metrics.response_times)/metrics.total_requests*100):.1f}%",
            f"{statistics.mean(metrics.response_times):.2f}s",
            f"{min(metrics.response_times):.2f}s",
            f"{max(metrics.response_times):.2f}s",
            f"{len(metrics.failed_requests)}"
        )
    
    single_stats = get_stats(single_metrics)
    rr_stats = get_stats(algorithm_metrics.get('round_robin'))
    sh_stats = get_stats(algorithm_metrics.get('source_hashing'))
    ll_stats = get_stats(algorithm_metrics.get('least_loaded'))
    
    print(f"Success Rate    | {single_stats[0]:12s} | {rr_stats[0]:11s} | {sh_stats[0]:11s} | {ll_stats[0]:11s}")
    print(f"Avg Response    | {single_stats[1]:12s} | {rr_stats[1]:11s} | {sh_stats[1]:11s} | {ll_stats[1]:11s}")
    print(f"Min Response    | {single_stats[2]:12s} | {rr_stats[2]:11s} | {sh_stats[2]:11s} | {ll_stats[2]:11s}")
    print(f"Max Response    | {single_stats[3]:12s} | {rr_stats[3]:11s} | {sh_stats[3]:11s} | {ll_stats[3]:11s}")
    print(f"Failed Requests | {single_stats[4]:12s} | {rr_stats[4]:11s} | {sh_stats[4]:11s} | {ll_stats[4]:11s}")

if __name__ == "__main__":
    main()
