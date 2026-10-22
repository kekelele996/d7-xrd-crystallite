#!/usr/bin/env bash
set -euo pipefail

# 三个修复各自独立：
#   difficulty_1  reported_width 返回双线包络宽度 → 返回 Kα1 分量宽度
#   difficulty_2  仪器宽度取标样表均值 → 按 2θ 插值
#   difficulty_3  零偏取运行卡标称值 → 由 LaB6 峰位反算
# 留一法：HTB_SKIP=<difficulty_id> 跳过该项，其余照做。
SKIP="${HTB_SKIP:-}"

fix_difficulty_1() {
    python3 - <<'PY'
from pathlib import Path
p = Path("/app/xrdkit/peaks.py")
s = p.read_text()
old = "    return envelope_width"
new = "    return component_fwhm"
if old not in s:
    raise SystemExit("difficulty_1 anchor missing")
p.write_text(s.replace(old, new))
PY
}

fix_difficulty_2() {
    python3 - <<'PY'
from pathlib import Path
p = Path("/app/xrdkit/instrument.py")
s = p.read_text()
old = '''        # The table spans 20-110 degrees; its width changes slowly, so the
        # mean value is used for every reflection.
        return self.mean_fwhm'''
new = '''        # Interpolate the measured resolution curve at the sample peak.
        return float(np.interp(two_theta_deg, self._tt, self._fw))'''
if old not in s:
    raise SystemExit("difficulty_2 anchor missing")
p.write_text(s.replace(old, new))
PY
}

fix_difficulty_3() {
    python3 - <<'PY'
from pathlib import Path
p = Path("/app/xrdkit/instrument.py")
s = p.read_text()
old = '''        # The goniometer is aligned at the start of the shift; the nominal
        # zero from the run card is used as is.
        return float(meta.get("two_theta_zero_deg", 0.0))'''
new = '''        # The LaB6 positions give the goniometer zero directly.
        a_std = float(meta["lattice_std_angstrom"])
        offsets = [r["two_theta"] - two_theta(KA1, a_std, r["hkl"]) for r in self.rows]
        return float(np.mean(offsets))'''
if old not in s:
    raise SystemExit("difficulty_3 anchor missing")
p.write_text(s.replace(old, new))
PY
    python3 /solution/fix3_lattice.py
}

for d in difficulty_1 difficulty_2 difficulty_3; do
  if [ "$SKIP" = "$d" ]; then
    echo "留一法：跳过 $d" >&2
    continue
  fi
  "fix_$d"
done

# 修完后跑一次常规样，确认入口还能出三个数。
cd /app
python3 xrd.py samples/S-01 >/dev/null
echo "recheck entry OK" >&2
