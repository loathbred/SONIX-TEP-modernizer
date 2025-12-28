import matplotlib.pyplot as plt
import numpy as np
from tkinter import messagebox
from matplotlib.backends.backend_pdf import PdfPages

#Disable default keymaps
plt.rcParams['keymap.save'] = []



#temporary shitty file input
#TODO take a directory and process all the files inside
#TODO make an old people friendly UI somehow instead of copy as file path 
#maybe just specify an input directory that is somehow saved once so that yun can set up once

#file_path = input("paste filepath: ").strip('"')


file_path = "C:\\Users\\alice\\Documents\\Schizofiles\\L0659.BP1"


#Open file and split into 2 binary objects, one for string data, and other for graph data
#CLOSES FILE produces string_data and FullYcords

graphstart = 0x4174
try:
    with open(file_path, 'rb') as f:
        string_data = np.frombuffer(f.read(graphstart), dtype=np.uint8)
        FullYcords = np.frombuffer(f.read(15325), dtype=np.int8)
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
f.close()

#dig around in string_data to pull info from addresses
string_list = np.empty(30, dtype=object)
label_list = np.array([
    'Class/Type:',
    'Nominal Freq. (MHz):',
    'Element Dim (in):',
    'Focal Length (in):',
    'Focus Type:',
    'Connector Type:',
    'Serial Numer:',
    'Test Taget:',
    'Test Material:',
    'Serial Number:',
    'Damping (Ohms):',
    'Energy Level:',
    'Attunation (dB):',
    'TITLE',
    'Gain (dB):',
    'High Pass Filter:',
    'Transmit (Vpp):'
    ])



fft_start = 0x5710-graphstart
fft_end = 0x5860 - graphstart
deltaX = 0.01
deltaF = 1 / ((n - 1) * 0.01)
fft = np.fft.fft(FullYcords[(fft_start):(fft_end)])
n = fft.len()
fft_half = fft[:(n//2)]
magnitude = np.abs(fft_half)


plt.ion() 
plt.plot(magnitude)
plt.xlabel('mhz')
plt.ylabel('arbs')
plt.title('Mhz')
plt.show(block=True)
"""
#interactive graphs
start_idx = 0
Xcoords = np.arange(512)
Ycords = FullYcords[start_idx:start_idx + 512]

# Oscilloscope Graph
plt.ion() #iniatalize interactive graph

fig1, ax1 = plt.subplots(num = 1)
line, = ax1.plot(Xcoords, Ycords)
ax1.set_ylim(FullYcords.min(), FullYcords.max())  # Fixed y-axis
plt.xlabel('Volts')
plt.ylabel('Microns(μ)')
plt.title('Digital Oscolloscope')


fig2, ax2 = plt.subplots(num = 2)
fft = np.fft.fft(Ycords)
magnitude = np.abs(fft)
line, = ax2.plot(magnitude)
plt.xlabel('Volts')
plt.ylabel('arbs')
plt.title('Mhz')

#GRaph UI
def on_key(event):
    global start_idx, line    
    if event.key == 'a':
        start_idx -= 20
        if start_idx < 0:
            start_idx = 0
    
    elif event.key == 'd':
        start_idx += 20
        if start_idx + 512 > len(FullXcords):
            start_idx = len(FullXcords) - 512
            if start_idx < 0:
                start_idx = 0
    elif event.key == 's':
        result = messagebox.askyesno("Save", "Do you want to save the Report as a PDF?")
        if result:
            print("User clicked Yes")
        else:
            print("User clicked No")

    else:
        return  # Ignore other keys
    
    # Update the view (O(1) slicing!)
    Ycords = FullYcords[start_idx:start_idx + 512]
    line.set_ydata(Ycords)
    ax1.set_title(f'View starting at index: {start_idx}')
    fig1.canvas.draw_idle()

# Connect the key press event
fig1.canvas.mpl_connect('key_press_event', on_key)

plt.show(block=True)  # Keep window open

"""


#"C:\Users\alice\Documents\Schizofiles\L0659.BP1"
#"C:\Users\alice\Documents\Schizofiles\L1232.BP1"