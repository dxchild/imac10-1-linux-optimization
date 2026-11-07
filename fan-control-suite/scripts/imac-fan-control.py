#!/usr/bin/env python3
"""iMac Fan Control — dark dashboard and response curves, read-only SMC UI."""
import json
import os
import subprocess
import tkinter as tk
from collections import deque
from pathlib import Path

CONFIG = Path.home() / ".config/imac-fan-curves.json"
SMC = next(iter(Path("/sys/devices/platform").glob("applesmc.*")), None)
COLORS = {"ODD": "#0A84FF", "HDD": "#30D158", "CPU": "#BF5AF2"}
HISTORY = {x: deque(maxlen=120) for x in ("GPU", "CHIPSET", "PSU")}
BG, CARD, FG, SECONDARY, GRID = "#111214", "#222327", "#f5f5f7", "#aaaab1", "#414247"
FONT = "Inter"
root = tk.Tk()
root.title("iMac Fan Control")
root.geometry("1000x940")
root.resizable(False, False)
canvas = tk.Canvas(root, width=1000, height=940, bg=BG, highlightthickness=0)
canvas.pack()
levels = {}
slider_areas = {}
reset_area = (818, 294, 968, 328)
dragging = None
save_after = None

def get_int(name):
    try:
        return int((SMC / name).read_text())
    except (OSError, ValueError, TypeError):
        return None

def temperatures():
    result = {}
    if SMC is not None:
        for label in SMC.glob("temp*_label"):
            try:
                code = label.read_text().strip()
                p = label.with_name(label.name.replace("_label", "_input"))
                value = float(p.read_text()) / 1000
                if 15 <= value <= 110:
                    result[code] = value
            except (OSError, ValueError):
                pass
    for hw in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (hw / "name").read_text().strip() != "coretemp":
                continue
            for p in hw.glob("temp*_input"):
                value = float(p.read_text()) / 1000
                if 15 <= value <= 110:
                    result["CORE_" + p.stem] = value
        except (OSError, ValueError):
            pass
    return result

def hottest(data, codes):
    vals = [data[x] for x in codes if x in data]
    return max(vals) if vals else None

def load():
    try:
        data = json.loads(CONFIG.read_text())
        return {k: max(0, min(100, int(data.get(k, 0)))) for k in COLORS}
    except (OSError, ValueError, TypeError, AttributeError):
        return {k: 0 for k in COLORS}

def save():
    global save_after
    save_after = None
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    dest = CONFIG.with_name(CONFIG.name + ".tmp")
    dest.write_text(json.dumps({key: v.get() for key, v in levels.items()}, indent=2)+"\n")
    os.replace(dest, CONFIG)

def text(x, y, value, size=11, color=FG, bold=False, anchor="nw"):
    canvas.create_text(x, y, text=value, anchor=anchor,
                       font=(FONT, size, "bold" if bold else "normal"), fill=color)

def box(x, y, w, h, color=CARD, r=16):
    x2, y2 = x+w, y+h
    p = [x+r,y, x2-r,y, x2,y, x2,y+r, x2,y2-r, x2,y2,
         x2-r,y2, x+r,y2, x,y2, x,y2-r, x,y+r, x,y]
    canvas.create_polygon(p, fill=color, outline="#36373c", width=1,
                          smooth=True, splinesteps=16)

def clamp(v):
    return max(0, min(1, v))

def pct(name, data):
    if name == "ODD":
        gpu = hottest(data, ("TG0D", "TG0H", "TG0P"))
        chip, psu = data.get("TN0H"), data.get("Tp2H")
        if None in (gpu, chip, psu):
            return 1.0
        return clamp((max(gpu, chip-5, psu)-45)/35)
    if name == "HDD":
        vals = [v for v in (hottest(data, ("TG0D","TG0H","TG0P")),
                            data.get("TN0H"), data.get("Tp2H"),
                            hottest(data, ("Tm0P","TM0P"))) if v is not None]
        return clamp((max(vals)-55)/35) if vals else 0
    vals = [v for v in (hottest(data, ("TC0D","TC0P","TC0H")), *[
        v for k,v in data.items() if k.startswith("CORE_")]) if v is not None]
    return clamp((max(vals)-55)/35) if vals else 0

CURVES = {
    "GPU": [(55,1200),(60,1500),(65,1800),(70,2200),(75,2700),(80,3300)],
    "Chipset": [(55,1200),(60,1350),(65,1500),(70,1900),(75,2400),(80,3000)],
    "PSU": [(50,1200),(55,1400),(60,1600),(65,1900),(70,2400),(75,3000)]
}
def model(name, fraction, data):
    n = {"ODD":1,"HDD":2,"CPU":3}[name]
    floor = {"ODD":1200,"HDD":1100,"CPU":940}[name]
    ceiling = get_int(f"fan{n}_max") or {"ODD":3800,"HDD":5500,"CPU":4600}[name]
    boost = round(floor + fraction*levels[name].get()/100*(ceiling-floor))
    if name != "ODD":
        return floor, boost, floor, ceiling
    # ODD shape is a model relative to today's sensor differences, not
    # the same as a controlled laboratory temperature sweep.
    gpu = hottest(data, ("TG0D","TG0H","TG0P"))
    chip, psu = data.get("TN0H"), data.get("Tp2H")
    if None in (gpu,chip,psu):
        return ceiling, ceiling, floor, ceiling
    reference = max(gpu, chip-5, psu)
    virtual = 45 + 35*fraction
    sensors = {"GPU":virtual+gpu-reference,
               "Chipset":virtual+chip-reference,
               "PSU":virtual+psu-reference}
    baseline = floor
    for group,temp in sensors.items():
        requested = ceiling
        for threshold,rpm in CURVES[group]:
            if temp < threshold:
                requested = rpm
                break
        baseline = max(baseline, requested)
    return baseline, max(baseline, boost), floor, ceiling

def chart(name, x, y, data):
    box(x,y,300,165)
    color = COLORS[name]
    level=levels[name].get()
    text(x+18,y+14,"Fan Response",12,bold=True)
    text(x+280,y+14,f"+{level}%",11,color,True,"ne")
    left,right,top,bottom = x+19,x+281,y+42,y+94
    for f in (0,0.5,1):
        yy=bottom-f*(bottom-top)
        canvas.create_line(left,yy,right,yy,fill=GRID,dash=(2,5))
    base,sel=[],[]
    for i in range(81):
        p=i/80
        orig,new,floor,ceil=model(name,p,data)
        a=max(1,ceil-floor)
        xx=left+(right-left)*p
        base.extend((xx,bottom-(orig-floor)/a*(bottom-top)))
        sel.extend((xx,bottom-(new-floor)/a*(bottom-top)))
    canvas.create_line(*base,fill="#92939a",width=2,dash=(4,4))
    canvas.create_line(*sel,fill=color,width=3)
    text(x+18,y+103,"45–80 °C" if name=="ODD" else "55–90 °C",10,SECONDARY)
    text(x+281,y+103,"RPM floor",10,SECONDARY,anchor="ne")
    a,b,yy=x+19,x+281,y+133
    canvas.create_line(a,yy,b,yy,fill="#515159",width=7,capstyle=tk.ROUND)
    xx=a+(b-a)*level/100
    if level:
        canvas.create_line(a,yy,xx,yy,fill=color,width=7,capstyle=tk.ROUND)
    canvas.create_oval(xx-10,yy-10,xx+10,yy+10,fill="#fff",outline="#bbb")
    text(x+18,y+145,"Default",10,SECONDARY)
    text(x+281,y+145,"Faster",10,SECONDARY,anchor="ne")
    slider_areas[name]=(a,yy-14,b,yy+14)

def cooling_running():
    try:
        r=subprocess.run(["systemctl","is-active","imac-odd-fan.service"],
                         text=True,capture_output=True,timeout=1)
        return r.stdout.strip()=="active"
    except (OSError,subprocess.TimeoutExpired):
        return False

def draw(capture=True):
    canvas.delete("all")
    slider_areas.clear()
    canvas.create_rectangle(0,0,1000,106,fill="#18191c",outline="")
    text(28,18,"iMac Fan Control",25,bold=True)
    text(28,69,"APPLE SMC / CUSTOM COOLING PROFILE",11,SECONDARY)
    text(968,34,"● Cooling Active" if cooling_running() else "● Service Inactive",
         12,"#30D158" if cooling_running() else "#FF9F0A",True,"ne")
    t=temperatures()
    vals=[
        ("GPU",hottest(t,("TG0D","TG0H","TG0P")),"#0A84FF"),
        ("CHIPSET",t.get("TN0H"),"#FFD60A"),
        ("POWER SUPPLY",t.get("Tp2H"),"#30D158"),
        ("CPU HEATSINK",t.get("TC0H"),"#BF5AF2")]
    text(28,126,"Temperatures",17,bold=True)
    for i,(name,value,color) in enumerate(vals):
        x=28+i*240
        box(x,159,220,118)
        canvas.create_oval(x+18,177,x+28,187,fill=color,outline="")
        text(x+38,175,name,11,SECONDARY,True)
        text(x+18,207,f"{value:.1f} °C" if value is not None else "N/A",23,bold=True)
        text(x+18,252,"LIVE SENSOR",10,SECONDARY)
    text(28,300,"Fans & Response Curves",17,bold=True)
    box(818,294,150,34,"#2a4563",12)
    text(893,311,"Reset to Default",10,bold=True,anchor="center")
    for i,name in enumerate(("ODD","HDD","CPU"),1):
        x=28+(i-1)*322
        color=COLORS[name]
        box(x,348,300,145)
        rpm=get_int(f"fan{i}_input")
        _,target,floor,ceil=model(name,pct(name,t),t)
        text(x+18,362,f"{name} FAN",12,color,True)
        text(x+18,393,f"{rpm} RPM" if rpm is not None else "N/A",22,bold=True)
        text(x+18,432,("Modeled target" if name=="ODD" else "Requested minimum")
             +f": {target} RPM",10,SECONDARY)
        text(x+18,457,"Software controlled" if name=="ODD" else "Firmware auto + boost",10,SECONDARY)
        canvas.create_line(x+18,480,x+282,480,fill="#505059",width=7)
        if rpm is not None:
            f=clamp((rpm-floor)/max(1,ceil-floor))
            if f>0:
                canvas.create_line(x+18,480,x+18+264*f,480,fill=color,width=7)
        chart(name,x,506,t)
    text(28,693,"Temperature History",17,bold=True)
    box(28,726,944,150)
    for key,value in (("GPU",vals[0][1]),("CHIPSET",vals[1][1]),("PSU",vals[2][1])):
        if capture:
            HISTORY[key].append(value)
    legends=(("GPU","#0A84FF"),("CHIPSET","#FFD60A"),("PSU","#30D158"))
    for temp in (40,60,80):
        yy=824-(temp-20)/80*78
        canvas.create_line(62,yy,949,yy,fill=GRID,dash=(2,5))
        text(52,yy,f"{temp}°",10,SECONDARY,anchor="e")
    for i,(name,color) in enumerate(legends):
        segment=[]
        for k,value in enumerate(HISTORY[name]):
            if value is None:
                if len(segment)>=4:
                    canvas.create_line(*segment,fill=color,width=2)
                segment=[]
                continue
            xx=62+k/119*887
            yy=824-(max(20,min(100,value))-20)/80*78
            segment.extend((xx,yy))
        if len(segment)>=4:
            canvas.create_line(*segment,fill=color,width=2)
        x=65+i*135
        canvas.create_oval(x,851,x+10,861,fill=color,outline="")
        text(x+16,850,"POWER SUPPLY" if name=="PSU" else name,10,SECONDARY)
    text(28,905,"0% = original cooling  •  sliders only increase fan response  •  2 s refresh",
         10,SECONDARY)

def schedule_save():
    global save_after
    if save_after is not None:
        root.after_cancel(save_after)
    save_after=root.after(400,save)

def update(name,x):
    a,_,b,_=slider_areas[name]
    percent=round(clamp((x-a)/(b-a))*20)*5
    if levels[name].get()!=percent:
        levels[name].set(percent)
        schedule_save()
        draw(False)

def on_click(e):
    global dragging
    dragging=None
    if 818<=e.x<=968 and 294<=e.y<=328:
        for v in levels.values():
            v.set(0)
        schedule_save()
        draw(False)
        return
    for name,(a,top,b,bottom) in slider_areas.items():
        if a-10<=e.x<=b+10 and top<=e.y<=bottom:
            dragging=name
            update(name,e.x)
            return

def on_drag(e):
    if dragging:
        update(dragging,e.x)

def on_release(e):
    global dragging
    dragging=None

for name,value in load().items():
    levels[name]=tk.IntVar(value=value)
canvas.bind("<Button-1>",on_click)
canvas.bind("<B1-Motion>",on_drag)
canvas.bind("<ButtonRelease-1>",on_release)

def tick():
    draw()
    root.after(2000,tick)
tick()
root.mainloop()
