#!/bin/bash
# Run on a Steam Deck (desktop mode, over SSH or in Konsole) against a playable Linux folder, e.g. one
# the Linux setup made. Phase 11e (docs/07-linux.md): frame rate and APU power in a quest. Screenshots,
# logs and samples go to ~/ss-delta-test/runs/<name>/ on the Deck (game-derived: never commit them).
#   DIR=<folder> [SETTINGS="frame_rate=30 scale=2"] [WRAP="gamescope -W 1280 -H 800 --"] \
#       bash deck-quest.sh <stage select index> <run name>
# The index is the quest's row in Stage Select (tools/questmaps.py; build/maps.txt), as in map-sweep.ps1.
# DIR defaults to ~/ss-delta-test/setup-test/ss-delta; FS (its Vita file system) to $DIR/fs; SLR runs it
# in another wrapper first (e.g. the Steam runtime's "run --"). BootSequence and the ini are restored.
k=${1:-0}
name=${2:-quest}
dir=${DIR:-$HOME/ss-delta-test/setup-test/ss-delta}
fs=${FS:-$dir/fs}
out=$HOME/ss-delta-test/runs/$name
cfg=$fs/ux0/app/PCSA00152/resource/config.ini
ini=$dir/ss-delta.ini
rm -rf "$out"; mkdir -p "$out"
cp "$ini" "$out/ss-delta.ini.before"
for kv in $SETTINGS; do sed -i "s/^${kv%%=*} = .*/${kv%%=*} = ${kv#*=}/" "$ini"; done
grep -nE "^(scale|frame_rate|fullscreen|vsync|window_size|filter) " "$ini" | tr '\n' ' '; echo
last=$(grep -n $'^BootSequence\t' "$cfg" | tail -1 | cut -d: -f1)
sed -i "${last}s/^BootSequence\t.*\r\$/BootSequence\tQuest Select\r/" "$cfg"

export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 DISPLAY=:0
export XAUTHORITY=$(ls /run/user/1000/xauth_* 2>/dev/null | head -1)
export VITA3K_FRAME_LOG="$out/frames.txt" VITA3K_INPUT_PIPE=ssd-input
fifo=/tmp/ssd-input
hw=$(dirname $(ls /sys/class/drm/card*/device/hwmon/hwmon*/power1_average | head -1))
(while sleep 1; do
    echo "$(date +%s) $(cat $hw/power1_average) $(grep -o '[0-9]*Mhz \*' /sys/class/drm/card*/device/pp_dpm_sclk | head -1 | cut -d' ' -f1) $(awk '{s+=$1} END {print int(s/NR/1000)}' /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq)"
done > "$out/power.txt") &
sampler=$!
cd "$dir"
$SLR $WRAP ./ss-delta.x86_64 > "$out/console.log" 2>&1 &

send() { timeout 5 sh -c "echo '$1' > $fifo" || echo "send failed: $1"; }
press() { send "hold $1"; sleep 0.15; send "hold"; sleep 0.3; }
hold() { send "hold $1"; sleep "$2"; send "hold"; sleep 0.3; }
axes() { send "axes $1"; sleep "$2"; send "axes 0 0 0 0"; sleep 0.3; }
shot() { send "screenshot $out/$1.png"; sleep 1; }
mark() { echo "$(date +%s) $1" >> "$out/steps.txt"; }

for i in $(seq 30); do [ -p $fifo ] && break; sleep 1; done
mark start; sleep 15; shot 0-stage-select
for i in 1 2 3 4 5 6; do press down; done
for i in $(seq $((k / 10))); do hold "r right" 0.3; done
for i in $(seq $((k % 10))); do press right; done
mark quest-start; press circle
sleep 40; mark loaded; shot 2-loaded
axes "0 0 1 0" 0.9
axes "0 -1 0 0" 2.5; mark walked; shot 4-walk
sleep 20; mark idle; shot 5-idle
alive=no; pgrep -x ss-delta.x86_64 >/dev/null && alive=yes
pkill -TERM -x ss-delta.x86_64; sleep 4; pkill -KILL -x ss-delta.x86_64 2>/dev/null
kill $sampler
cp "$out/ss-delta.ini.before" "$ini"
sed -i "${last}s/^BootSequence\t.*\r\$/BootSequence\tTitle\r/" "$cfg"
cp "$dir/ss-delta/vita3k.log" "$out/" 2>/dev/null
echo "running at the end: $alive"
journalctl -k --since "-3 min" --no-pager | grep -E "ring .*timeout" | cut -c1-140
# the last 20 s in the quest (after "walked"): frame rate from the frame log, power from the sampler
python3 - "$out" <<'EOF'
import sys, os
out = sys.argv[1]
steps = dict(l.split()[1::-1] for l in open(os.path.join(out, 'steps.txt')))
t0, t1 = int(steps['walked']), int(steps['idle'])
ms = [float(l.split(',')[1]) for l in open(os.path.join(out, 'frames.txt')).read().split('\n')[1:] if l]
tail, acc = [], 0
for m in reversed(ms):
    acc += m; tail.append(m)
    if acc > 20000: break
p = [l.split() for l in open(os.path.join(out, 'power.txt')) if len(l.split()) == 4]
p = [(int(a), int(b) / 1e6, int(c[:-3]), int(d)) for a, b, c, d in p if t0 <= int(a) <= t1]
if p:
    print(f'quest, last 20 s: {1000 * len(tail) / sum(tail):.1f} fps (worst {max(tail):.1f} ms); '
          f'APU {sum(x[1] for x in p) / len(p):.2f} W, GPU {sum(x[2] for x in p) / len(p):.0f} MHz, '
          f'CPU {sum(x[3] for x in p) / len(p):.0f} MHz')
EOF
