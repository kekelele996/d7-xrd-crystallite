# 陶瓷粉体衍射复检

陶瓷粉体每批抽一个样做 X 射线衍射复检，复检单要三个数：晶粒尺寸、微应变、晶格常数。样品是立方萤石结构的氧化物粉体，衍射峰的指标由批次卡给出，每批的晶格常数在 5.39 到 5.42 埃之间。

`/app/xrd.py` 是上一班留下的快速工具，给一个运行目录就往标准输出打一行 JSON。这两周它在粗晶、细晶和退火三类批次上都出过偏差：粗晶批次的尺寸报到工艺记录的两倍多，细晶批次的尺寸也偏大，退火批次的晶格常数和随附标样对不上，超差 0.1% 以上。`/app/samples/` 下有两份带证书的常规样，证书只给晶粒尺寸和晶格常数，可以拿来自测。

## 输入

`python3 /app/xrd.py <运行目录>`

运行目录里有三个文件：

- `sample.csv`：两列 `two_theta_deg,counts`，2θ 从 20° 到 110°，步长 0.005°。
- `instrument.csv`：标样峰表，列 `h,k,l,two_theta_deg,fwhm_deg`。标样是 LaB6，晶格常数在 `meta.json` 的 `lattice_std_angstrom`。
- `meta.json`：`wavelength_ka1_angstrom`、`wavelength_ka2_angstrom`、`ka2_intensity_ratio`、`scherrer_k`、`two_theta_zero_deg`（运行卡上的标称零偏）、`lattice_std_angstrom`、`phase`。

`/app/samples/` 下有两份样例，目录结构相同。

## 输出

标准输出一个 JSON 对象，只有三个字段：

```json
{"size_nm": 42.0, "strain_pct": 0.12, "lattice_a_angstrom": 5.407}
```

- `size_nm`：晶粒尺寸，单位 nm。
- `strain_pct`：微应变，单位百分点（0.05 表示 0.05%）。
- `lattice_a_angstrom`：立方晶格常数，单位 Å。

## 要求

- 晶粒尺寸相对误差不超过 12%，微应变绝对误差不超过 0.05 个百分点，晶格常数相对误差不超过 0.02%。
- 一个运行目录 20 秒内出结果。
- 只读运行目录，不往目录里写文件；不联网。
- 同一份输入重复执行，结果一致。
