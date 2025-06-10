import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Sample: replace this with your actual RefereeState data
from python import fsds

client = fsds.FSDSClient()
client.confirmConnection()
refState = client.getRefereeState()
cones = refState.cones
initial = refState.initial_position
print(initial.x, initial.y)
car_path = []



# Organize cones by color
def organize_cones(cones):
    blue, yellow, orange = [], [], []
    for cone in cones:
        point = (cone['x'], cone['y'])
        if cone['color'] == 0:
            blue.append(point)
        elif cone['color'] == 1:
            yellow.append(point)
        elif cone['color'] == 2:
            orange.append(point)
    return blue, yellow, orange


blue_cones, yellow_cones, orange_cones = organize_cones(cones)

# GUI setup
root = tk.Tk()
root.title("Cone Viewer")

# Create the figure
fig, ax = plt.subplots(figsize=(10, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)


# Plot function
def draw_plot():
    ax.clear()

    # 🔁 Get updated referee state
    refState = client.getRefereeState()
    cones = refState.cones
    initial = refState.initial_position

    # 🔁 Rebuild cone groups
    blue_cones, yellow_cones, orange_cones = [], [], []
    for cone in cones:
        pt = (cone['x'], cone['y'])
        if cone['color'] == 0:
            blue_cones.append(pt)
        elif cone['color'] == 1:
            yellow_cones.append(pt)
        elif cone['color'] == 2:
            orange_cones.append(pt)
            # print(pt)

    # 🟦 Draw updated cones
    if show_blue.get() and blue_cones:
        xs, ys = zip(*blue_cones)
        ax.scatter(xs, ys, c='blue', label='Blue cones')
    if show_yellow.get() and yellow_cones:
        xs, ys = zip(*yellow_cones)
        ax.scatter(xs, ys, c='gold', label='Yellow cones')
    if show_orange.get() and orange_cones:
        xs, ys = zip(*orange_cones)
        ax.scatter(xs, ys, c='orange', label='Orange cones')

    # 🔴 Initial position
    ax.scatter(initial.x, initial.y, c='red', marker='*', s=100, label='Initial Position')

    # 🟢 Live car position
    car_pos = client.getCarState().kinematics_estimated.position
    car_x = initial.x + car_pos.x_val
    car_y = initial.y + car_pos.y_val
    ax.scatter(car_x, car_y, c='green', marker='o', s=100, label='Car Position', zorder=5)
    print(f"Car position: x = {car_x:.2f}, y = {car_y:.2f}")

    # 📦 Auto-rescale view
    all_x = [p[0] for p in blue_cones + yellow_cones + orange_cones] + [car_x]
    all_y = [p[1] for p in blue_cones + yellow_cones + orange_cones] + [car_y]
    margin = 50
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    ax.axis('equal')
    ax.set_title("RefereeState Cone Map (Live)")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()
    ax.grid(True)
    canvas.draw()



# Checkbuttons to toggle cone visibility
frame = tk.Frame(root)
frame.pack()

show_blue = tk.BooleanVar(value=True)
show_yellow = tk.BooleanVar(value=True)
show_orange = tk.BooleanVar(value=True)

tk.Checkbutton(frame, text="Blue", variable=show_blue, command=draw_plot).pack(side=tk.LEFT)
tk.Checkbutton(frame, text="Yellow", variable=show_yellow, command=draw_plot).pack(side=tk.LEFT)
tk.Checkbutton(frame, text="Orange", variable=show_orange, command=draw_plot).pack(side=tk.LEFT)

draw_plot()

def update():
    draw_plot()
    root.after(200, update)  # Call again every 200 ms

update()  # Start the loop
root.mainloop()

