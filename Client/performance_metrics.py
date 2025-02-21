class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.failed_requests = 0
        self.total_requests = 0
        
    def record_request(self, start_time, end_time=None):
        self.total_requests += 1
        if end_time:
            self.response_times.append(end_time - start_time)
        else:
            self.failed_requests += 1
            
    def print_summary(self, phase_name):
        print(f"\n{'-'*20} {phase_name} Summary {'-'*20}")
        
        if self.total_requests == 0:
            print("No requests recorded")
            return
            
        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)
            min_response = min(self.response_times)
            max_response = max(self.response_times)
            success_rate = (len(self.response_times) / self.total_requests) * 100
            
            print(f"Total Requests: {self.total_requests}")
            print(f"Successful Requests: {len(self.response_times)}")
            print(f"Failed Requests: {self.failed_requests}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Average Response Time: {avg_response:.2f}s")
            print(f"Minimum Response Time: {min_response:.2f}s")
            print(f"Maximum Response Time: {max_response:.2f}s")
        else:
            print("No successful requests recorded")
        print("-" * 60)