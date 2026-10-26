import subprocess, sys, array, math
f = sys.argv[1]; win = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
sr = 16000
raw = subprocess.run(["ffmpeg","-v","error","-i",f,"-vn","-ac","1","-ar",str(sr),"-f","s16le","-"],capture_output=True).stdout
a = array.array("h"); a.frombytes(raw)
n = int(sr*win); out = []
for i in range(0, len(a), n):
    seg = a[i:i+n]
    if not seg: break
    rms = math.sqrt(sum(x*x for x in seg)/len(seg))/32768
    out.append(f"{i/sr:.1f}:{(20*math.log10(rms) if rms>0 else -99):.0f}")
print(" ".join(out))
