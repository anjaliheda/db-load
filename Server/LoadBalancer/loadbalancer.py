from flask import Flask, request, jsonify
import requests
import itertools
import hashlib
import random
import time

app = Flask(__name__)

# Server configuration
servers = ["http://server1:5000", "http://server2:5000", "http://server3:5000", "http://server4:5000"]
current_algorithm = "round_robin"

# Round robin iterator
server_pool = itertools.cycle(servers)

# Server state tracking
server_states = {
    server: {
        'healthy': True,
        'last_check': time.time(),
        'consecutive_failures': 0,
        'current_load': 0
    } for server in servers
}

def is_server_healthy(server):
    """Check server health and update state"""
    try:
        response = requests.get(f"{server}/health", timeout=2)
        server_states[server]['last_check'] = time.time()
        
        if response.status_code == 200:
            server_states[server]['healthy'] = True
            server_states[server]['consecutive_failures'] = 0
            return True
        elif response.status_code == 503:  # Server reports it's overloaded
            server_states[server]['current_load'] = response.json().get('current_load', 999)
            return False
        else:
            server_states[server]['consecutive_failures'] += 1
            if server_states[server]['consecutive_failures'] > 3:
                server_states[server]['healthy'] = False
            return False
    except:
        server_states[server]['consecutive_failures'] += 1
        if server_states[server]['consecutive_failures'] > 3:
            server_states[server]['healthy'] = False
        return False

def get_server_load(server):
    """Get current load of a server"""
    try:
        response = requests.get(f"{server}/load", timeout=1)
        if response.status_code == 200:
            load = response.json().get('load', 0)
            server_states[server]['current_load'] = load
            return load
    except:
        pass
    return server_states[server]['current_load']

def choose_server_round_robin():
    """Round-robin server selection"""
    for _ in range(len(servers)):
        server = next(server_pool)
        if is_server_healthy(server):
            return server
    return None

def choose_server_hash(request_data):
    """Source IP hashing-based server selection"""
    # Create a composite key from multiple request parameters
    key = str(request_data.get('task_type', '')) + \
          str(request_data.get('num1', '')) + \
          str(request_data.get('num2', '')) + \
          str(request_data.get('text', ''))
    
    # Try servers in hash-determined order
    hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
    start_idx = hash_val % len(servers)
    
    for i in range(len(servers)):
        idx = (start_idx + i) % len(servers)
        server = servers[idx]
        if is_server_healthy(server):
            return server
    return None

def choose_server_least_loaded():
    """Least-loaded server selection"""
    # Update load information for all servers
    for server in servers:
        if is_server_healthy(server):
            get_server_load(server)
    
    # Choose the healthy server with minimum load
    min_load = float('inf')
    chosen_server = None
    
    for server in servers:
        if server_states[server]['healthy']:
            load = server_states[server]['current_load']
            if load < min_load:
                min_load = load
                chosen_server = server
    
    return chosen_server

@app.route('/set_algorithm', methods=['POST'])
def set_algorithm():
    global current_algorithm
    data = request.json
    algo = data.get('algorithm', 'round_robin')
    
    if algo in ["round_robin", "source_hashing", "least_loaded"]:
        current_algorithm = algo
        return jsonify({"message": f"Algorithm set to {algo}"})
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

@app.route('/request', methods=['POST'])
def route_request():
    if current_algorithm == "round_robin":
        server = choose_server_round_robin()
    elif current_algorithm == "source_hashing":
        server = choose_server_hash(request.json)
    elif current_algorithm == "least_loaded":
        server = choose_server_least_loaded()
    else:
        server = choose_server_round_robin()
    
    if not server:
        return jsonify({"error": "No healthy servers available"}), 503
    
    try:
        response = requests.post(
            f"{server}/request",
            json=request.json,
            timeout=10
        )
        return response.json(), response.status_code
    except Exception as e:
        server_states[server]['consecutive_failures'] += 1
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    healthy_servers = sum(1 for server in servers if is_server_healthy(server))
    return jsonify({
        "status": "healthy" if healthy_servers > 0 else "critical",
        "healthy_servers": healthy_servers,
        "algorithm": current_algorithm
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)