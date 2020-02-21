"""tracé du signale audio en temps réel avec wxmatplotlib.

wx Matplotlib and NumPy have to be installed.

"""
import queue
import sys

import numpy as np
import sounddevice as sd
import wx
import wx.lib.newevent
import fenetrecourbe as fc

class FluxAudio:
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self, freq=44100, fenetre=2048, canaux=2):
        self.nb_ech_fenetre = fenetre
        self.nb_canaux = canaux
        self.tps_refresh = 0.05
        self.Fe = freq
        self.courbe = None
        length = int(self.nb_ech_fenetre*2)
        self.plotdata = np.zeros((length, self.nb_canaux))
        self.mapping = [c-1  for c in range(self.nb_canaux)]  # Channel numbers start with 1
        self.q = queue.Queue()
        self.stream = None

    def open(self):
        self.stream = sd.InputStream(
            device=None, channels=self.nb_canaux-1,
            samplerate=self.Fe, callback=audio_callback)
        self.stream.start()

    def close(self):
        self.stream.stop()
        self.stream.close()

def audio_callback(indata, _frames, _time, status):
    """Focntion appelée lorsque des données audio sont disponibles."""
    global fa
    if status:
        print(status, file=sys.stderr)
    # Copie des données dans la file:
    fa.q.put(indata[:, fa.mapping])
    # Création d'un événement
    evt = new_event(attr1="audio_callback", attr2=0)
    # Envoi de l'événement à la fenêtre chargée du tracé
    wx.PostEvent(fa.courbe, evt)


try:
    application = wx.App()
    new_event, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()
    fa = FluxAudio()
    frame = wx.Frame(None, -1, 'Mes Courbes')
    plotter = fc.PlotNotebook(frame, fa, evt_type=EVT_SOME_NEW_EVENT)
    page1 = plotter.add('figure 1')
    fa.courbe = plotter
    frame.Show()
    print(sd.query_devices())
    device = None
    device_info = sd.query_devices(None, 'input')
    Fe = device_info['default_samplerate']
    fa.open()

    application.MainLoop()
except Exception as e:
    print(type(e).__name__ + ': ' + str(e))
