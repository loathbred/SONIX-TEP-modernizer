import matplotlib.pyplot as plt
import os
import numpy as np
import re
from tkinter import messagebox
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path

#Disable default keymaps
plt.rcParams['keymap.save'] = []

#easy access
STRINGSTARTADDRESS = 0x3C48  
labels = {
    0: "Class/Type",
    1: "Nominal Freq. (MHz)",
    2: "Element Dim (in)",
    3: "Focal Length (in)",
    4: "Focus Type",
    5: "Connector Type",
    6: "Serial Number",
    7: "",
    8: "Test Target",
    9: "Test Material",
    10: "",
    11: "",
    12: "Serial Number",
    13: "Damping (Ohms)",
    14: "Energy Level",
    15: "Attenuation (dB)",
    16: "Gain (dB)",
    17: "High Pass Filter",
    18: "Transmit (Vpp)",
    19: "",
    20: "",
    21: "",
}


#Function for iterating through all files and seeing data at a certain location
def file_TEST(file_path, target_location, target_size):
    file_type = file_path.split('.', 1)[1]
    if file_type == "BP1":
        try:
            with open(file_path, 'rb') as f:
                f.seek(target_location)
                data = np.frombuffer(f.read(target_size), dtype=np.uint8).tobytes().decode('utf-8',errors = 'replace')
            return (data)
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        f.close()
        
#testing functons for iterating through multiple files
def file_TESTnum(file_path, target_location, target_size):
    try:
        file_type = file_path.split('.', 1)[1]
        if file_type == "BP1":
            try:
                with open(file_path, 'rb') as f:
                    f.seek(target_location)
                    data = np.frombuffer(f.read(target_size), dtype=np.int8)
                return (data)
            except FileNotFoundError:
                print(f"Error: The file '{file_path}' was not found.")
            except Exception as e:
                print(f"An error occurred: {e}")
            f.close()
    except Exception as e:
        print(e)

def mass_text(directory, location, size, numbers):
    c = 0
    print("address: " + str(hex(location)) + ", size: " + str(size))
    for filepath in directory.iterdir():
        if filepath.is_file():
            if (not numbers):
                temp = file_TEST(str(filepath), location, size)
            else:
                temp = file_TESTnum(str(filepath), location, size)
            if not temp is None:
                print(c, end = ": ")
                #print(filepath, end = ": ")
                print(temp)
            c+= 1


"""
TODO take a directory and process all the files inside
TODO make an old people friendly UI somehow instead of copy as file path 
maybe just specify an input directory that is somehow saved once so that yun can set up once
Open file and split into 2 binary objects, one for string data, and other for graph data
CLOSES FILE produces string_data and FullYcords
"""
def file_pull(graphstart, file_path):
    file_type = file_path.split('.', 1)[1]
    try:
        with open(file_path, 'rb') as f:
            string_data = np.frombuffer(f.read(graphstart), dtype=np.uint8)
            FullYcords = np.frombuffer(f.read(15325), dtype=np.int8)
        return (string_data, FullYcords * -1, file_type)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    f.close()


#dig around in string_data to pull info from addresses
def extra_data(string_data):
    string_list = np.empty(22, dtype=object)
    misc_strings = np.empty(10, dtype = object)
    position_string = string_data[0x82A:0x84c].tobytes().decode('utf-8',errors = 'replace')
    vpp_string = string_data[0x85E:0x867].tobytes().decode('utf-8',errors = 'replace')
    pack = string_data[0xE08:0xE1F]

    print("signal location string",position_string)
    match = re.search(r',([^I]*?)In', position_string)
    if match:
        signal_location = int(float(match.group(1).strip()) * 1000) + 0

    vpp = float(vpp_string.strip().rstrip('\x00'))

    for i in range(22):
        start = STRINGSTARTADDRESS + (i * 20)
        string_list[i] = string_data[start:start+20].tobytes().decode('utf-8',errors = 'replace').strip()

    for(i) in range(22):
        print(labels[i] + ": " + string_list[i])

    misc_strings[0] = string_data[0x3E00:0x3E00 + 20].tobytes().decode('utf-8',errors = 'replace').strip() #Title
    misc_strings[1] = string_data[0x3EE0:0x3EE0 + 20].tobytes().decode('utf-8',errors = 'replace').strip() #Equipment
    return(string_list, signal_location, vpp, pack,  misc_strings)


def pack_decode(pack):
    start_pos = pack[2:4].view(np.uint16)[0] * .01
    gate_length = pack[22].view(np.uint8)
    gate_high = float(pack[4].view(np.uint8)) / 256.0
    gate_low = float(pack[5].view(np.uint8)) / 256.0
    return  [start_pos, gate_length, gate_high, gate_low]

#find the first signal
def find_signal(FullYcords, pack):
    gate_length_us = pack[22] / 10.0                            # 1.5 µs
    start_samples = (pack[3] << 8) | (pack[13] & 0xFF)          # 929 samples
    high_threshold = pack[5] / 255.0 * 100                      # ~85% 
    low_threshold = pack[4] / 255.0 * 100   
    



#oscilloscope graph
def digital_oscilloscope(FullYcords, vpp):
    #interactive graphs
    X0 = 0
    sampling_rate = 1
    Xcoords = np.arange(X0, X0 + 512) * sampling_rate
    Ycords = FullYcords[start_idx:start_idx + 512]
    max = float(np.max(Ycords))
    min = float(np.min(Ycords))
    temp =(abs(max) + abs(min))
    deltaY = vpp/temp
    Ycords = Ycords * deltaY
    print("DeltaY",deltaY)
    print("GraphStart",start_idx)
    # Oscilloscope Graph
    plt.ion() #iniatalize interactive graph

    fig, ax1 = plt.subplots(num = 1)
    line, = ax1.plot(Xcoords, Ycords)
    ax1.set_ylim(max * deltaY * 1.2, min * deltaY *1.2)  # Fixed y-axis
    plt.ylabel('Volts')
    plt.xlabel('Micro seconds(μ)')
    plt.title('Digital Oscilloscope')
    return (fig, ax1, line)


#fast fourier transformation graph
def fft_graph(FullYcords, fft_start):
    sample_size = 512
    sampling_rate = 100 #MHz
    fft_end = fft_start + sample_size
    fft = np.fft.fft(FullYcords[(fft_start):(fft_end)])
    n = len(fft)
    fft_half = fft[:(n//2)]
    magnitude = np.abs(fft_half) 
    deltaX = sampling_rate / sample_size
    MHz = np.arange(256) * deltaX

    fig2 = plt.figure()
    plt.plot(MHz, magnitude)
    plt.xlim(0,5)
    plt.xlabel('mhz')
    plt.ylabel('arbs')
    plt.title('Mhz')
    plt.show(block=True)


#GRaph UI
def on_key(event):
    global start_idx, line    
    if event.key == 'a':
        start_idx -= 20
        if start_idx < 0:
            start_idx = 0
    
    elif event.key == 'd':
        start_idx += 20
        if start_idx + 512 > len(FullYcords):
            start_idx = len(FullYcords) - 512
            if start_idx < 0:
                start_idx = 0
    elif event.key == 's':
        result = messagebox.askyesno("FFT", "transform")
        if result:
            fft_graph(FullYcords, start_idx)
        else:
            print("User clicked No")

    else:
        return  # Ignore other keys
    
    # Update the view (O(1) slicing!)
    Ycords = FullYcords[start_idx:start_idx + 512]
    line.set_ydata(Ycords)
    ax1.set_title(f'View starting at index: {start_idx}')
    fig.canvas.draw_idle()



#MAIN METHOD

graph_start = 0x4174
file_path =  input("paste filepath: ").strip('"')
string_data, FullYcords, file_type = file_pull(graph_start, file_path)
if(file_type == "BP1"):
    string_list, signal_location, vpp, pack, misc_strings = extra_data(string_data)
    #start_idx = signal_location 
    start_idx = find_signal(FullYcords, pack)
    fig, ax1, line = digital_oscilloscope(FullYcords, vpp)
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show(block=True)  # Keep window open
elif(file_type == "BP2"):
    print("unimplemented")


#"C:\Users\alice\Documents\Mover\DAC\D0616.BP1"

"""#directory = Path("C:\\Users\\alice\\Documents\\Mover\\DAC")
directory = Path("C:\\Users\\alice\\Documents\\tep files")

#PACKED GATE DATA
location = 0xE08
size = 24
numbers = True


mass_text(directory, location, size, numbers)"""


