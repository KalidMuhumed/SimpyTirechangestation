import simpy
import random
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Funktion för att omvandla minuter till klockslag (används för att visa x-axeln i timmar)
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
        # Justera ankomstfrekvensen beroende på om det är rusningstid
        is_rush_hour = rush_hour_start <= env.now <= rush_hour_end
        if is_rush_hour:
            # Introducera variation i ankomstfrekvensen under rush hour
            arrival_variability = random.uniform(0.8, 1.2)  # ±20% variation
            current_arrival_rate = rush_hour_rate * arrival_variability
        else:
            current_arrival_rate = normal_rate
        
        # Samla in kölängd och resursutnyttjande varje minut för att täcka hela simuleringstiden
        queue_lengths.append(len(tire_station.num_employees.queue))
        resource_utilization.append(tire_station.num_employees.count / tire_station.num_employees.capacity)
        
        if is_rush_hour:
            rush_queue_lengths.append(len(tire_station.num_employees.queue))
            rush_resource_utilization.append(tire_station.num_employees.count / tire_station.num_employees.capacity)
        
        # Vänta en minut innan nästa kund anländer (för att få kontinuerliga data)
        yield env.timeout(1)  # Insamling av data varje minut
        if random.random() < 1.0 / current_arrival_rate:  # Kontrollera om en kund anländer
            customer_id += 1
            env.process(customer(env, customer_id, tire_station, max_wait_time))

def run_simulation(sim_time, num_employees, tire_change_time, rush_hour_rate, normal_rate, rush_hour_start, rush_hour_end, max_wait_time):
    global waiting_times, operation_times, queue_lengths, resource_utilization, turnaways, total_customers
    global rush_queue_lengths, rush_resource_utilization
    # Rensa datalistor för ny körning
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

    # Beräkna genomsnittliga värden för att visa i konsolen
    avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    avg_operation_time = sum(operation_times) / len(operation_times) if operation_times else 0
    avg_queue_length = sum(queue_lengths) / len(queue_lengths) if queue_lengths else 0
    avg_utilization = sum(resource_utilization) / len(resource_utilization) if resource_utilization else 0
    avg_rush_queue_length = sum(rush_queue_lengths) / len(rush_queue_lengths) if rush_queue_lengths else 0
    avg_rush_utilization = sum(rush_resource_utilization) / len(rush_resource_utilization) if rush_resource_utilization else 0

    # Skriv ut resultaten i terminalen
    print(f"\nResults for {employees} employee(s):")
    print(f"Average Waiting Time: {avg_waiting_time:.2f} mins")
    print(f"Average Operation Time: {avg_operation_time:.2f} mins")
    print(f"Average Queue Length: {avg_queue_length:.2f} customers")
    print(f"Resource Utilization: {avg_utilization:.2%}")
    print(f"Total Turnaways: {turnaways}")
    print(f"Average Rush Hour Queue Length: {avg_rush_queue_length:.2f} customers")
    print(f"Average Rush Hour Utilization: {avg_rush_utilization:.2%}")


    # Visualization i en kompakt vertikal layout
    fig, axs = plt.subplots(3, 1, figsize=(6, 8))  # Mindre figurstorlek
    fig.subplots_adjust(hspace=0.4)  # Mindre mellanrum mellan grafer

    # Första grafen - Waiting Time Distribution
    axs[0].hist(waiting_times, bins=5, color='#4c72b0', edgecolor='black', alpha=0.7)
    axs[0].set_title(f"Waiting Time Distribution ({employees} Employee(s))", fontsize=10, fontweight='bold')
    axs[0].set_xlabel("Waiting Time (minutes)", fontsize=8, fontweight='bold')
    axs[0].set_ylabel("Customers", fontsize=8, fontweight='bold')

    # Andra grafen - Queue Length over Time
    axs[1].plot(queue_lengths, color='#c44e52', linewidth=1.2)
    axs[1].set_title(f"Queue Length over Time ({employees} Employee(s))", fontsize=10, fontweight='bold')
    axs[1].set_xlabel("Time of Day", fontsize=8, fontweight='bold')
    axs[1].set_ylabel("Queue Length", fontsize=8, fontweight='bold')
    axs[1].xaxis.set_major_formatter(FuncFormatter(time_formatter))
    axs[1].set_xlim(0, SIM_TIME)
    axs[1].axvline(x=RUSH_HOUR_START, color='orange', linestyle='--', linewidth=1, label='Rush Hour Start')
    axs[1].axvline(x=RUSH_HOUR_END, color='purple', linestyle='--', linewidth=1, label='Rush Hour End')
    axs[1].legend(loc="upper right", bbox_to_anchor=(1.1, 1), fontsize="x-small")

    # Tredje grafen - Resource Utilization over Time
    axs[2].plot(resource_utilization, color='#55a868', linewidth=1.2)
    axs[2].set_title(f"Resource Utilization over Time ({employees} Employee(s))", fontsize=10, fontweight='bold')
    axs[2].set_xlabel("Time of Day", fontsize=8, fontweight='bold')
    axs[2].set_ylabel("Utilization (%)", fontsize=8, fontweight='bold')
    axs[2].xaxis.set_major_formatter(FuncFormatter(time_formatter))
    axs[2].set_xlim(0, SIM_TIME)
    axs[2].axvline(x=RUSH_HOUR_START, color='orange', linestyle='--', linewidth=1, label='Rush Hour Start')
    axs[2].axvline(x=RUSH_HOUR_END, color='purple', linestyle='--', linewidth=1, label='Rush Hour End')
    axs[2].legend(loc="upper right", bbox_to_anchor=(1.1, 1), fontsize="x-small")

    plt.tight_layout()
    plt.show()

