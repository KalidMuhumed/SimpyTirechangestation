import simpy
import random
import matplotlib.pyplot as plt

# Constants
SIM_TIME = 180         # Total simulation time in minutes
TIRE_CHANGE_TIME = 5  # Average time to change tires (minutes)
ARRIVAL_RATE = 3     # Average arrival rate (customers per minute)
MAX_WAIT_TIME = 5      # Maximum time a customer can wait before leaving

# Data Collection
waiting_times = []      # List of waiting times for each customer
operation_times = []    # List of operation times (tire change) for each customer
turnaways = 0           # Count of customers who couldn't wait and left
total_customers = 0     # Total customers served

class TireStation:
    def __init__(self, env, num_employees, tire_change_time):
        self.env = env
        # Resource for the number of employees available for tire changes
        self.num_employees = simpy.Resource(env, num_employees)
        self.tire_change_time = tire_change_time

    def change_tires(self, customer):
        """Process for changing tires."""
        yield self.env.timeout(random.expovariate(1.0 / self.tire_change_time))

def customer(env, customer_id, tire_station, max_wait_time):
    """Customer process: arrives, waits, and may leave if wait is too long."""
    global turnaways, total_customers
    arrival_time = env.now
    with tire_station.num_employees.request() as request:
        # Wait for an available employee or time out if the wait is too long
        result = yield request | env.timeout(max_wait_time)
        if request in result:
            # Customer begins tire change
            wait_time = env.now - arrival_time
            waiting_times.append(wait_time)
            start_operation_time = env.now
            yield env.process(tire_station.change_tires(customer_id))
            operation_time = env.now - start_operation_time
            operation_times.append(operation_time)
            total_customers += 1  # Increment the total customers served
        else:
            # Customer leaves due to long wait time
            turnaways += 1

def setup(env, num_employees, tire_change_time, arrival_rate, max_wait_time):
    """Sets up the tire change station and generates customers."""
    tire_station = TireStation(env, num_employees, tire_change_time)
    customer_id = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / arrival_rate))
        customer_id += 1
        env.process(customer(env, customer_id, tire_station, max_wait_time))

def run_simulation(sim_time, num_employees, tire_change_time, arrival_rate, max_wait_time):
    """Runs the tire change station simulation."""
    global waiting_times, operation_times, turnaways, total_customers
    waiting_times, operation_times, turnaways, total_customers = [], [], 0, 0
    env = simpy.Environment()
    env.process(setup(env, num_employees, tire_change_time, arrival_rate, max_wait_time))
    env.run(until=sim_time)
    return waiting_times, operation_times, turnaways, total_customers

# Number of repetitions for each scenario
num_repetitions = 5

# Run and visualize results for both scenarios (1 and 2 employees)
for employees in [1, 2]:
    total_turnaways = 0
    total_waiting_times = []
    total_operation_times = []
    total_customers_arrived = 0

    for _ in range(num_repetitions):
        waiting_times, operation_times, turnaways, customers_arrived = run_simulation(
            SIM_TIME, employees, TIRE_CHANGE_TIME, ARRIVAL_RATE, MAX_WAIT_TIME
        )
        total_turnaways += turnaways
        total_waiting_times.extend(waiting_times)
        total_operation_times.extend(operation_times)
        total_customers_arrived += (waiting_times.count(0) + total_customers + turnaways)  # Count all attempts

    # Calculate averages
    avg_waiting_time = sum(total_waiting_times) / len(total_waiting_times) if total_waiting_times else 0
    avg_operation_time = sum(total_operation_times) / len(total_operation_times) if total_operation_times else 0

    # Print the results
    print(f"\nRunning simulation with {employees} employee(s):")
    print(f"Total Turnaways: {total_turnaways}")
    print(f"Average waiting time: {avg_waiting_time:.2f} minutes")
    print(f"Average operation time: {avg_operation_time:.2f} minutes")
    print(f"Total customers arrived in this scenario: {total_customers_arrived}")

    # Visualization code with updated figure size and subplot arrangement
    plt.figure(figsize=(8, 4))

    # Plot the distribution of waiting times
    plt.subplot(2, 2, 1)
    plt.hist(total_waiting_times, bins=10, edgecolor='black', color='#4c72b0', alpha=0.5)
    plt.title('Distribution of Waiting Times', fontsize=10, fontweight='bold')
    plt.xlabel('Waiting Time (minutes)', fontsize=9, fontname='Times New Roman')
    plt.ylabel('Number of Customers', fontsize=8)
    plt.xticks(fontsize=7)
    plt.yticks(fontsize=7)

    # Plot the distribution of operation times
    plt.subplot(2, 2, 2)
    plt.hist(total_operation_times, bins=10, edgecolor='black', color='#55a868', alpha=0.5)
    plt.title('Distribution of Operation Times', fontsize=10, fontweight='bold')
    plt.xlabel('Operation Time (minutes)', fontsize=9,fontname='Times New Roman')
    plt.ylabel('Number of Customers', fontsize=8)
    plt.xticks(fontsize=7)
    plt.yticks(fontsize=7)

    # Plot the distribution of turnaways 
    plt.subplot(2, 2, 3)
    plt.bar(["cars"], [total_turnaways], color='#c44e52', edgecolor='black', alpha=0.7, width=0.3 )
    plt.xlabel('Total Turnways', fontsize=10,fontweight='bold')
    plt.ylabel('Number of Customers', fontsize=8)
    plt.xticks(fontsize=7)
    plt.yticks(fontsize=7)

    # Show plots
    plt.tight_layout()
    plt.savefig(f'performance_metrics_{employees}_employees.png', dpi=1080)
    plt.show()
