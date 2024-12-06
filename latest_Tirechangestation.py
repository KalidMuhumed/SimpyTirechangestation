import simpy
import random
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def time_formatter(x, pos):
    hours = int(x // 60) + 6  # Startar från 06:00
    return f"{hours:02d}:00"

# Konstanter
SIM_TIME = 600  # Total simuleringstid i minuter (10 timmar från 06:00 till 16:00)
TIRE_CHANGE_TIME = 8
RUSH_HOUR_RATE = 5  # Ankomstfrekvens under rusningstid (kunder per minut)
NORMAL_RATE = 3     # Ankomstfrekvens under vanliga tider (kunder per minut)
RUSH_HOUR_START = 300  # Starttid för rusningstid i minuter (11:00)
RUSH_HOUR_END = 360    # Sluttid för rusningstid i minuter (12:00)
MAX_WAIT_TIME = 5

# Global data collection lists
waiting_times = []
operation_times = []
queue_lengths = []
resource_utilization = []
turnaways = 0
total_customers = 0
rush_queue_lengths = []
rush_resource_utilization = []

class TireStation:
    def __init__(self, env, num_employees, tire_change_time):
        self.env = env
        self.num_employees = simpy.Resource(env, num_employees)
        self.tire_change_time = tire_change_time

    def change_tires(self, customer):
        yield self.env.timeout(random.expovariate(1.0 / self.tire_change_time))

def customer(env, customer_id, tire_station, max_wait_time):
    global turnaways, total_customers
    arrival_time = env.now
    with tire_station.num_employees.request() as request:
        result = yield request | env.timeout(max_wait_time)
        if request in result:
            wait_time = env.now - arrival_time
            waiting_times.append(wait_time)
            start_operation_time = env.now
            yield env.process(tire_station.change_tires(customer_id))
            operation_time = env.now - start_operation_time
            operation_times.append(operation_time)
            total_customers += 1
        else:
            turnaways += 1

def setup(env, num_employees, tire_change_time, rush_hour_rate, normal_rate, rush_hour_start, rush_hour_end, max_wait_time):
    tire_station = TireStation(env, num_employees, tire_change_time)
    customer_id = 0
    while True:
        is_rush_hour = rush_hour_start <= env.now <= rush_hour_end
        if is_rush_hour:
            arrival_variability = random.uniform(0.8, 1.2)  # ±20% variation
            current_arrival_rate = rush_hour_rate * arrival_variability
        else:
            current_arrival_rate = normal_rate
        
        queue_lengths.append(len(tire_station.num_employees.queue))
        resource_utilization.append(tire_station.num_employees.count / tire_station.num_employees.capacity)
        
        if is_rush_hour:
            rush_queue_lengths.append(len(tire_station.num_employees.queue))
            rush_resource_utilization.append(tire_station.num_employees.count / tire_station.num_employees.capacity)
        
        yield env.timeout(1)
        if random.random() < 1.0 / current_arrival_rate:
            customer_id += 1
            env.process(customer(env, customer_id, tire_station, max_wait_time))

def run_simulation(sim_time, num_employees, tire_change_time, rush_hour_rate, normal_rate, rush_hour_start, rush_hour_end, max_wait_time):
    global waiting_times, operation_times, queue_lengths, resource_utilization, turnaways, total_customers
    global rush_queue_lengths, rush_resource_utilization
    waiting_times, operation_times, queue_lengths, resource_utilization, turnaways, total_customers = [], [], [], [], 0, 0
    rush_queue_lengths, rush_resource_utilization = [], []
    
    env = simpy.Environment()
    env.process(setup(env, num_employees, tire_change_time, rush_hour_rate, normal_rate, rush_hour_start, rush_hour_end, max_wait_time))
    env.run(until=sim_time)
    return waiting_times, operation_times, queue_lengths, resource_utilization, turnaways, total_customers, rush_queue_lengths, rush_resource_utilization

# Simulering för 1, 2 och 3 anställda
for employees in [1, 2, 3]:  
    waiting_times, operation_times, queue_lengths, resource_utilization, turnaways, total_customers, rush_queue_lengths, rush_resource_utilization = run_simulation(
        SIM_TIME, employees, TIRE_CHANGE_TIME, RUSH_HOUR_RATE, NORMAL_RATE, RUSH_HOUR_START, RUSH_HOUR_END, MAX_WAIT_TIME
    )

    avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    avg_queue_length = sum(queue_lengths) / len(queue_lengths) if queue_lengths else 0
    avg_utilization = sum(resource_utilization) / len(resource_utilization) if resource_utilization else 0
    avg_rush_queue_length = sum(rush_queue_lengths) / len(rush_queue_lengths) if rush_queue_lengths else 0

    print("\nSimulation Metrics:")
    print(f"- Employees: {employees}")
    print(f"- Avg Waiting Time: {avg_waiting_time:.2f} mins")
    print(f"- Avg Queue Length: {avg_queue_length:.2f}")
    print(f"- Utilization: {avg_utilization:.2%}")
    print(f"- Total Turnaways: {turnaways}")
    print(f"- Avg Rush Hour Queue: {avg_rush_queue_length:.2f}")

            
        # Visualization for each employee case
    fig, axs = plt.subplots(2, 1, figsize=(5, 6))  # Smaller and compact figure size
    fig.subplots_adjust(hspace=0.3)  # Reduce vertical space between graphs

    # Queue Length Over Time
    axs[0].plot(queue_lengths, color='#c44e52', linewidth=1.2)
    axs[0].set_title(f"Queue Length Over Time (Employees: {employees})", fontsize=12, fontweight='bold')  # Bold title
    axs[0].set_xlabel("Time (minutes)", fontsize=10, fontweight='bold')  # Bold x-axis label
    axs[0].set_ylabel("Queue Length", fontsize=10, fontweight='bold')  # Bold y-axis label
    axs[0].xaxis.set_major_formatter(FuncFormatter(time_formatter))
    axs[0].tick_params(axis='both', labelsize=10)  # Larger tick labels
    axs[0].axvline(x=RUSH_HOUR_START, color='orange', linestyle='--', linewidth=1, label='Rush Start')  # Vertical line for Rush Start
    axs[0].axvline(x=RUSH_HOUR_END, color='purple', linestyle='--', linewidth=1, label='Rush End')  # Vertical line for Rush End
    axs[0].legend(loc="upper right", fontsize=8)  # Simple legend with only the labels

    # Resource Utilization Over Time
    axs[1].plot(resource_utilization, color='#55a868', linewidth=1.2)
    axs[1].set_title(f"Resource Utilization Over Time (Employees: {employees})", fontsize=12, fontweight='bold')  # Bold title
    axs[1].set_xlabel("Time (minutes)", fontsize=10, fontweight='bold')  # Bold x-axis label
    axs[1].set_ylabel("Utilization (%)", fontsize=10, fontweight='bold')  # Bold y-axis label
    axs[1].xaxis.set_major_formatter(FuncFormatter(time_formatter))
    axs[1].tick_params(axis='both', labelsize=10)  # Larger tick labels
    axs[1].axvline(x=RUSH_HOUR_START, color='orange', linestyle='--', linewidth=1, label='Rush Start')  # Vertical line for Rush Start
    axs[1].axvline(x=RUSH_HOUR_END, color='purple', linestyle='--', linewidth=1, label='Rush End')  # Vertical line for Rush End
    axs[1].legend(loc="upper right", fontsize=8)  # Simple legend with only the labels

    plt.tight_layout()
    plt.show()






