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


#dig around in string_data to pull usable variables from addresses
def extra_data(string_data):
    string_list = np.empty(22, dtype=object)
    misc_strings = np.empty(10, dtype = object)
    position_string = string_data[0x82A:0x84c].tobytes().decode('utf-8',errors = 'replace')
    vpp_string = string_data[0x85E:0x867].tobytes().decode('utf-8',errors = 'replace')
    pack = string_data[0xE08:0xE1F]
    gate_data = string_data[0x900:0x96f]

    match = re.search(r'WP:([\d.]+)', position_string)
    if match:
        signal_location = (float(match.group(1).strip()))
    print("signal location string",signal_location)


    vpp = float(vpp_string.strip().rstrip('\x00'))

    for i in range(22):
        start = STRINGSTARTADDRESS + (i * 20)
        string_list[i] = string_data[start:start+20].tobytes().decode('utf-8',errors = 'replace').strip()

    #for(i) in range(22): ##
    #    print(labels[i] + ": " + string_list[i])

    misc_strings[0] = string_data[0x3E00:0x3E00 + 20].tobytes().decode('utf-8',errors = 'replace').strip() #Title
    misc_strings[1] = string_data[0x3EE0:0x3EE0 + 20].tobytes().decode('utf-8',errors = 'replace').strip() #Equipment
    return(string_list, signal_location, vpp, pack, misc_strings, gate_data)


#find the first signal
def find_signal(FullYcords, low_threshold):
    print("lgate",low_threshold * 0.001960784688995215) ##
    i = 0 
    for e in FullYcords:
        if (e < low_threshold):
            print (i)
            return i
        i+= 1

#calculate DeltaY based on the Vpp and the max and min of the signal graph
def find_DeltaY (FullYcords, vpp):
    max = float(np.max(FullYcords))
    min = float (np.min(FullYcords))
    temp =(max + abs(min))
    return (vpp/temp, max, min)

#decode gate data
def gate_decode (gate_data):
    gate_length = gate_data[32:36].view('<u4')[0]
    low_gate = gate_data[36:40].view('<i4')[0]
    gate_start = gate_data[68:72].view('<u4')[0]
    gate_end = gate_start + gate_length
    return (gate_start, gate_end, low_gate, gate_length)

#oscilloscope graph
def digital_oscilloscope(FullYcords, deltaY, start_idx, max, min, signal_location):
    #interactive graphs
    t0 = signal_location 
    sampling_rate = .005
    Xcoords = np.arange(t0, t0 + (511 * sampling_rate), sampling_rate)
    Ycords = FullYcords[start_idx:start_idx + 512]
    Ycords = Ycords * deltaY
    print("DeltaY",deltaY) ##
    print("GraphStart",start_idx) ##
    

    #iniatalize interactive graph
    plt.ion() 
    fig, ax1 = plt.subplots(num = 1)
    line, = ax1.plot(Xcoords, Ycords)
    ax1.set_ylim(max * deltaY * 1.2, min * deltaY *1.2)  # Fixed y-axis
    plt.ylabel('Volts')
    plt.xlabel('Micro seconds(μ)')
    plt.title('Digital Oscilloscope')
    return (fig, ax1, line)


#fast fourier transformation graph
def fft_graph(FullYcords, fft_start, gate_length):
    print("fft start: ",fft_start)
    print("gate length: ",gate_length)
    sample_size = gate_length
    sampling_rate = 100 #MHz
    fft_end = fft_start + sample_size
    fft = np.fft.fft(FullYcords[(fft_start):(fft_end)])
    n = len(fft)
    fft_half = fft[:(n//2)]
    magnitude = np.abs(fft_half) 
    deltaX = sampling_rate / sample_size
    MHz = np.arange(int(sample_size/2)) * deltaX

    fig2 = plt.figure()
    plt.plot(MHz, magnitude)
    plt.xlim(0,5)
    plt.xlabel('mhz')
    plt.ylabel('arbs')
    plt.title('Mhz')
    plt.show(block=True)



#MAIN METHOD

graph_start = 0x4174
file_path =  input("paste filepath: ").strip('"')
string_data, FullYcords, file_type = file_pull(graph_start, file_path)
if(file_type == "BP1"):
    string_list, signal_location, vpp, pack, misc_strings, gate_data = extra_data(string_data)
    deltaY, max, min = find_DeltaY(FullYcords, vpp)
    gate_start, gate_end, low_gate, gate_length =gate_decode(gate_data)
    start_idx = find_signal(FullYcords, low_gate)
    fig, ax1, line = digital_oscilloscope(FullYcords, deltaY, start_idx, max, min, signal_location)
    
    plt.show(block=True)  # Keep window open
elif(file_type == "BP2"):
    print("unimplemented")





#"C:\Users\alice\Documents\Mover\DAC\D0616.BP1"

"""#directory = Path("C:\\Users\\alice\\Documents\\Mover\\DAC")
directory = Path("C:\\Users\\alice\\Documents\\tep files")
mass_text(directory, location, size, numbers)"""


"""#GRaph UI
def on_key(event):
    if event.key == 's':
        result = messagebox.askyesno("FFT", "transform")
        if result:
            fft_graph(FullYcords, gate_start, gate_length)
        else:
            print("User clicked No")"""