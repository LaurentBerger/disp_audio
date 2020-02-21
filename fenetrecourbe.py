import time
import queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx
import wx.lib.newevent
import wx.lib.agw.aui as aui


class Plot(wx.Panel):
    """
    Fenetage wx contenant un graphique matplotlib
    """
    def __init__(self, parent, fa, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.fa = fa
        self.parent = parent
        self.figure, self.ax = plt.subplots()
        self.lines = self.ax.plot(fa.plotdata)
        self.ax.legend(['channel {}'.format(c) for c in range(self.fa.nb_canaux)],
                       loc='lower left', ncol=self.fa.nb_canaux)
        self.ax.axis((0, len(self.fa.plotdata)/2, -1, 1))
        self.ax.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)

    def draw_page(self):
        """Tracer de la fenêtre en fonction
        du signal audio
        """
        while True:
            try:
                data = self.fa.q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            self.fa.plotdata = np.roll(self.fa.plotdata, -shift, axis=0)
            self.fa.plotdata[-shift:, :] = data
        for column, line in enumerate(self.lines):
            line.set_ydata((column+1) *self.fa.plotdata[:, column])
        return self.lines


class PlotNotebook(wx.Panel):
    def __init__(self, parent, fa, id=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id)
        self.fa = fa
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.page = []
        self.SetSizer(sizer)
        self.parent = parent
        self.Bind(evt_type, self.draw_page)
        self.clock = 0

    def add(self, name="plot"):
        """ Ajout d'un onglet au panel
        """
        page = Plot(self.nb, self.fa)
        self.page.append(page)
        self.nb.AddPage(page, name)
        return page

    def draw_page(self, _evt):
        """ tracé de la courbe associé à l'onglet
        """
        if time.clock() - self.clock < self.fa.tps_refresh:
            return
        self.clock = time.clock()
        for page in self.page:
            if self.nb.GetCurrentPage() == page:
                page.draw_page()
                page.canvas.draw()
