import wave
import sys
import numpy
import time

import pyaudio

# CHUNK = 1
bose_volume = 100
ewa_volume = 100
jbl_volume = 10

bose_latency = 0.25
ewa_latency = 0
jbl_latency = 0

# CHUNK = 128
# CHUNK = 1024
# CHUNK = 4096
CHUNK = 65536

def audio_datalist_set_volume(datalist, volume):
    """ Change value of list of audio chunks """
    sound_level = (volume / 100.)

    chunk = numpy.frombuffer(datalist, numpy.int16)

    chunk = (chunk * sound_level)

    chunkBytes = chunk.astype(numpy.int16).tobytes()
    return chunkBytes

if len(sys.argv) < 2:
    print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
    sys.exit(-1)

databuffer = bytearray()

with wave.open(sys.argv[1], 'rb') as wf:
    # Instantiate PyAudio and initialize PortAudio system resources (1)

    while len(data := wf.readframes(CHUNK)):  # Requires Python 3.8+ for :=
        databuffer.extend(data)

    p = pyaudio.PyAudio()

    bose_device_id = jbl_device_id = ewa_device_id = 0

    for idx in range(p.get_device_count()):
        d = p.get_device_info_by_index(idx)
        name = d.get('name').lower()
        if "bose" in name and bose_device_id == 0:
            bose_device_id = idx
        elif "jbl" in name and jbl_device_id == 0:
            jbl_device_id = idx
        elif "ewa audio a150 stereo" in name and ewa_device_id == 0:
            ewa_device_id = idx
    
    ewa_progress = 0    # use it directly, update it by +4*CHUNK
    jbl_progress = 0    # use it directly, update it by +4*CHUNK
    bose_progress = 0    # use it directly, update it by +4*CHUNK

    def ewa_callback(in_data, frame_count, time_info, status):
        global ewa_progress, ewa_latency, wf
        if ewa_latency > 0:
            ewa_latency -= (frame_count/wf.getframerate())
            return (bytes(bytearray(frame_count*4)), pyaudio.paContinue)
        data = databuffer[ewa_progress:ewa_progress+4*frame_count]
        data = audio_datalist_set_volume(data, ewa_volume)
        ewa_progress += 4*frame_count
        return (data, pyaudio.paContinue)
    
    def jbl_callback(in_data, frame_count, time_info, status):
        global jbl_progress, jbl_latency, wf
        if jbl_latency > 0:
            jbl_latency -= (frame_count/wf.getframerate())
            return (bytes(bytearray(frame_count*4)), pyaudio.paContinue)
        data = databuffer[jbl_progress:jbl_progress+4*frame_count]
        # print(jbl_progress)
        data = audio_datalist_set_volume(data, jbl_volume)
        jbl_progress += 4*frame_count
        return (data, pyaudio.paContinue)
    
    def bose_callback(in_data, frame_count, time_info, status):
        global bose_progress, bose_latency, wf
        if bose_latency > 0:
            bose_latency -= (frame_count/wf.getframerate())
            return (bytes(bytearray(frame_count*4)), pyaudio.paContinue)
        data = databuffer[bose_progress:bose_progress+4*frame_count]
        data = audio_datalist_set_volume(data, bose_volume)
        bose_progress += 4*frame_count
        return (data, pyaudio.paContinue)

    # Open stream (2)
    bose = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=int(wf.getframerate()),
                    output=True,
                    output_device_index=bose_device_id,
                    stream_callback=bose_callback)
    jbl = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=int(wf.getframerate()),
                    output=True,
                    output_device_index=jbl_device_id,
                    stream_callback=jbl_callback)
    # ewa = p.open(format=p.get_format_from_width(wf.getsampwidth()),
    #                 channels=wf.getnchannels(),
    #                 rate=int(wf.getframerate()),
    #                 output=True,
    #                 output_device_index=ewa_device_id,
    #                 stream_callback=ewa_callback)

    while bose.is_active() or jbl.is_active():
        time.sleep(0.1)
    
    # Close stream (4)
    
    bose.close()
    jbl.close()

    # Release PortAudio system resources (5)
    p.terminate()

