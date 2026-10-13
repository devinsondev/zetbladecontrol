"""ZET Blade Control — Windows Tkinter RGB editor."""
import json
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from pathlib import Path

from blade_protocol import BladeDevice, KEYS, MODES, PALETTE, effect_packet, custom_packets, validate_color

ROWS = [KEYS[:16], KEYS[16:37], KEYS[37:58], KEYS[58:74], KEYS[74:91], KEYS[91:]]
BACKGROUND = "#121825"
PANEL = "#1D2737"
TEXT = "#EAF1FF"
ACCENT = "#54C7FF"
DEFAULT = "#3A8CFF"

class App:
    def __init__(self, root):
        self.root=root
        self.root.title("ZET Blade Control")
        self.root.geometry("1190x730")
        self.root.minsize(900,600)
        self.root.configure(bg=BACKGROUND)
        self.device=BladeDevice()
        self.colors=[DEFAULT]*104
        self.pen=DEFAULT
        self.widgets=[]
        self.status=tk.StringVar(value="Disconnected — preview mode")
        self.mode=tk.StringVar(value="Static")
        self.palette=tk.StringVar(value="Blue")
        self.rainbow=tk.BooleanVar(value=False)
        self.speed=tk.IntVar(value=2)
        self.brightness=tk.IntVar(value=4)
        self._ui()
        self.root.protocol("WM_DELETE_WINDOW",self.close)

    def _button(self, parent, title, action, **kw):
        return tk.Button(parent,text=title,command=action,bg=PANEL,fg=TEXT,
                         activebackground="#34465D",activeforeground=TEXT,
                         relief="flat",cursor="hand2",padx=12,pady=8,**kw)

    def _ui(self):
        head=tk.Frame(self.root,bg=BACKGROUND)
        head.pack(fill="x",padx=22,pady=(18,8))
        tk.Label(head,text="ZET / BLADE",font=("Segoe UI",21,"bold"),
                 fg=TEXT,bg=BACKGROUND).pack(side="left")
        self._button(head,"Connect USB",self.connect).pack(side="right",padx=4)
        self._button(head,"Disconnect",self.disconnect).pack(side="right",padx=4)

        tabs=ttk.Notebook(self.root)
        tabs.pack(fill="both",expand=True,padx=20,pady=8)
        self.effects=tk.Frame(tabs,bg=BACKGROUND)
        self.editor=tk.Frame(tabs,bg=BACKGROUND)
        tabs.add(self.effects,text="  Hardware effects  ")
        tabs.add(self.editor,text="  Per-key RGB editor  ")
        self._effect_ui()
        self._editor_ui()

        footer=tk.Frame(self.root,bg=BACKGROUND)
        footer.pack(fill="x",padx=22,pady=(0,16))
        tk.Label(footer,textvariable=self.status,fg=ACCENT,bg=BACKGROUND,
                 anchor="w",font=("Segoe UI",10)).pack(side="left",fill="x",expand=True)
        tk.Label(footer,text="2EA8:2125 • manual writes only • no streaming",
                 fg="#9BA9BD",bg=BACKGROUND).pack(side="right")

    def _effect_ui(self):
        panel=tk.Frame(self.effects,bg=BACKGROUND)
        panel.pack(anchor="nw",padx=32,pady=30)
        self._caption(panel,"DEVICE EFFECTS")
        tk.Label(panel,text="Select a built-in effect, then click Apply.",
                 fg="#9BA9BD",bg=BACKGROUND).pack(anchor="w",pady=(0,18))
        r=tk.Frame(panel,bg=BACKGROUND)
        r.pack(anchor="w",pady=6)
        tk.Label(r,text="Effect",bg=BACKGROUND,fg=TEXT,width=14,anchor="w").pack(side="left")
        ttk.Combobox(r,textvariable=self.mode,values=list(MODES),state="readonly",width=24).pack(side="left")
        r=tk.Frame(panel,bg=BACKGROUND)
        r.pack(anchor="w",pady=6)
        tk.Label(r,text="Color",bg=BACKGROUND,fg=TEXT,width=14,anchor="w").pack(side="left")
        ttk.Combobox(r,textvariable=self.palette,values=list(PALETTE),
                     state="readonly",width=24).pack(side="left")
        tk.Checkbutton(panel,text="Rainbow / random where supported",
                       variable=self.rainbow,bg=BACKGROUND,fg=TEXT,
                       selectcolor=PANEL,activebackground=BACKGROUND).pack(anchor="w",pady=12)
        for title,variable in (("Speed",self.speed),("Brightness",self.brightness)):
            r=tk.Frame(panel,bg=BACKGROUND)
            r.pack(anchor="w",pady=9)
            tk.Label(r,text=title,bg=BACKGROUND,fg=TEXT,width=14,anchor="w").pack(side="left")
            tk.Scale(r,from_=0,to=4,orient="horizontal",variable=variable,
                     bg=BACKGROUND,fg=TEXT,highlightthickness=0,length=280,
                     troughcolor=PANEL).pack(side="left")
        self._button(panel,"Apply effect to keyboard",self.apply_effect).pack(anchor="w",pady=20)
        tk.Label(panel,text="Static mode supports 7 hardware colors only. Custom RGB is in the other tab.",
                 fg="#9BA9BD",bg=BACKGROUND,wraplength=650,justify="left").pack(anchor="w")

    def _caption(self,parent,title):
        tk.Label(parent,text=title,fg=ACCENT,bg=BACKGROUND,
                 font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(0,8))

    def _editor_ui(self):
        tool=tk.Frame(self.editor,bg=BACKGROUND)
        tool.pack(fill="x",padx=15,pady=14)
        self._button(tool,"Pick paint color",self.pick_color).pack(side="left",padx=3)
        self.swatch=tk.Label(tool,text=self.pen,bg=self.pen,fg="#FFFFFF",
                             width=10,font=("Segoe UI",10,"bold"))
        self.swatch.pack(side="left",padx=6)
        self._button(tool,"Paint all",self.fill_all).pack(side="left",padx=3)
        self._button(tool,"Clear / black",lambda:self.fill_all("#000000")).pack(side="left",padx=3)
        self._button(tool,"Save JSON",self.save).pack(side="right",padx=3)
        self._button(tool,"Load JSON",self.load).pack(side="right",padx=3)

        outer=tk.Frame(self.editor,bg=BACKGROUND)
        outer.pack(fill="both",expand=True,padx=12)
        canvas=tk.Canvas(outer,bg=BACKGROUND,highlightthickness=0)
        scroll=ttk.Scrollbar(outer,orient="vertical",command=canvas.yview)
        inner=tk.Frame(canvas,bg=BACKGROUND)
        window=canvas.create_window((0,0),window=inner,anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure(window,width=e.width))
        index=0
        for keys in ROWS:
            line=tk.Frame(inner,bg=BACKGROUND)
            line.pack(anchor="w",pady=5)
            for name in keys:
                i=index
                short=name.replace("Num","N",1) if name.startswith("Num") else name
                width=6 if len(short)>4 else 5
                button=tk.Button(line,text=short,width=width,height=2,
                                 bg=self.colors[i],fg="white",relief="raised",
                                 font=("Segoe UI",9),cursor="hand2",
                                 command=lambda j=i:self.paint(j))
                button.pack(side="left",padx=2)
                self.widgets.append(button)
                index+=1
        controls=tk.Frame(self.editor,bg=BACKGROUND)
        controls.pack(fill="x",padx=18,pady=12)
        self._button(controls,"Apply 104-key RGB profile",self.apply_custom).pack(side="left",padx=3)
        tk.Label(controls,text="Click keys to paint; nothing is sent until Apply.",
                 bg=BACKGROUND,fg="#9BA9BD").pack(side="left",padx=15)

    def report_error(self,exc):
        self.status.set("Error: "+str(exc))
        messagebox.showerror("ZET Blade Control",str(exc))

    def connect(self):
        try:
            self.device.connect()
            self.status.set("Connected to 2EA8:2125 — ready")
        except Exception as exc:
            self.report_error(exc)

    def disconnect(self):
        self.device.close()
        self.status.set("Disconnected")

    def apply_effect(self):
        try:
            packet=effect_packet(self.mode.get(),self.palette.get(),
                                 self.speed.get(),self.brightness.get(),self.rainbow.get())
            self.device.send([packet])
            self.status.set("Effect applied: "+self.mode.get())
        except Exception as exc:
            self.report_error(exc)

    def pick_color(self):
        _,color=colorchooser.askcolor(color=self.pen,parent=self.root)
        if color:
            self.pen=validate_color(color)
            self.swatch.configure(text=self.pen,bg=self.pen)

    def paint(self,index):
        self.colors[index]=self.pen
        self.widgets[index].configure(bg=self.pen)
        self.status.set("Painted "+KEYS[index]+" (preview only)")

    def fill_all(self,color=None):
        value=color or self.pen
        for i in range(104):
            self.colors[i]=value
            self.widgets[i].configure(bg=value)
        self.status.set("Filled preview; click Apply to send")

    def apply_custom(self):
        try:
            packets=custom_packets(self.colors,self.brightness.get())
            self.device.send(packets)
            self.status.set("104-key profile applied (%d HID packets)"%len(packets))
        except Exception as exc:
            self.report_error(exc)

    def save(self):
        filename=filedialog.asksaveasfilename(defaultextension=".json",
                  filetypes=[("JSON profiles","*.json")],title="Save keyboard profile")
        if filename:
            Path(filename).write_text(json.dumps({"format":"zetblade-v1","colors":self.colors},
                                                  indent=2),encoding="utf-8")
            self.status.set("Saved "+filename)

    def load(self):
        filename=filedialog.askopenfilename(filetypes=[("JSON profiles","*.json")])
        if not filename:
            return
        try:
            profile=json.loads(Path(filename).read_text(encoding="utf-8"))
            colors=profile["colors"]
            if len(colors)!=104:
                raise ValueError("Profile must contain exactly 104 colors")
            colors=[validate_color(c) for c in colors]
            for i,color in enumerate(colors):
                self.colors[i]=color
                self.widgets[i].configure(bg=color)
            self.status.set("Loaded preview — click Apply to send")
        except Exception as exc:
            self.report_error(exc)

    def close(self):
        self.device.close()
        self.root.destroy()

if __name__=="__main__":
    window=tk.Tk()
    App(window)
    window.mainloop()
