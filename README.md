# OpenSplat 参数测试指南

本文档介绍如何使用自动化脚本测试 OpenSplat 不同参数配置下的建模效果。

## 文件说明

| 文件 | 用途 | 预计耗时 |
|------|------|----------|
| `opensplat_param_test.py` | 完整参数测试（22个配置） | 2-4小时 |
| `quick_test.py` | 快速测试（7个核心配置） | 10-15分钟 |
| `compare_results.py` | 结果分析与对比 | 即时 |

## 快速开始


### 链接opensplat

```bash
ln -s path/to/opensplat .
```

### 多 GPU 并行测试（推荐）

如果你有多张 GPU，可以使用并行模式大幅缩短测试时间：

```bash
# 使用 4 个并行进程（适合双 Ada 6000，每张卡跑 2 个）
python3 quick_test.py -p 4

# 使用 4 个并行进程运行完整测试
python3 opensplat_param_test.py -p 4

# 指定输出目录
python3 opensplat_param_test.py -p 4 -o ./parallel_results

# 自动确认，无需交互
python3 opensplat_param_test.py -p 4 --yes
```

### 1. 快速测试（推荐先运行）

```bash
# 串行运行
python3 quick_test.py

# 并行运行（如有双 Ada 6000，推荐 -p 4）
python3 quick_test.py -p 4
```

这会运行 7 个关键参数组合的测试：
- 默认参数（baseline）
- 快速预览配置
- 高分辨率配置
- 不同球谐函数阶数
- 不同 SSIM 权重
- 不同细化频率
- 不同梯度阈值

输出将保存在 `./output_quick/` 目录。

### 2. 完整参数测试

```bash
# 串行运行
python3 opensplat_param_test.py

# 并行运行（如有双 Ada 6000，推荐 -p 4）
python3 opensplat_param_test.py -p 4
```

这会运行 22 个测试用例，覆盖所有重要参数。输出将保存在 `./output/` 目录。

**注意:** 完整测试耗时较长，建议使用并行模式。

### 3. 结果对比分析

```bash
# 分析完整测试结果
python3 compare_results.py ./output

# 分析快速测试结果
python3 compare_results.py ./output_quick
```

## 参数详解

### 核心参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--num-iters` | 30000 | 训练迭代次数，更多迭代通常更好但耗时更长 |
| `--downscale-factor` | 1 | 图像缩放因子，1=原始分辨率，2=1/2分辨率 |
| `--sh-degree` | 3 | 球谐函数阶数，控制视角相关光照效果 |
| `--ssim-weight` | 0.2 | SSIM损失权重，0=纯L1损失，更高更注重结构 |

### 高斯优化参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--refine-every` | 100 | 每隔多少步进行高斯分裂/复制/修剪 |
| `--densify-grad-thresh` | 0.0002 | 触发细化的梯度阈值，越低越敏感 |
| `--densify-size-thresh` | 0.01 | 大/小高斯的分界尺寸 |
| `--warmup-length` | 500 | 预热步数，之后才开始细化 |

### 预设配置建议

#### 快速预览
```bash
./opensplat -o preview.ply \
    --downscale-factor 4 \
    --num-iters 5000 \
    --sh-degree 1 \
    --refine-every 200 \
    banana/
```

#### 平衡配置（推荐）
```bash
./opensplat -o balanced.ply \
    --downscale-factor 2 \
    --num-iters 30000 \
    banana/
```

#### 高质量配置
```bash
./opensplat -o quality.ply \
    --downscale-factor 1 \
    --num-iters 50000 \
    --sh-degree 3 \
    --refine-every 50 \
    --densify-grad-thresh 0.0001 \
    banana/
```

## 结果解读

### PLY 文件大小
- **文件大小** ≈ 高斯点数量 × 每个高斯的数据量
- 更大的文件通常意味着更多细节，但渲染更慢

### 关键观察指标

1. **迭代次数影响**: 对比 `iters_10000` vs `iters_50000`
   - 观察收敛程度
   - 评估质量提升与时间的权衡

2. **分辨率影响**: 对比 `scale_1` vs `scale_4`
   - 观察细节保留程度
   - 评估训练速度差异

3. **球谐函数影响**: 对比 `sh_1` vs `sh_3`
   - 观察视角相关光照效果
   - 镜面反射、半透明效果

4. **SSIM权重影响**: 对比 `ssim_0` vs `ssim_0.5`
   - 观察结构保真度
   - 边缘清晰度

5. **细化频率影响**: 对比 `refine_50` vs `refine_200`
   - 观察高斯点数量差异
   - 细节丰富程度

## 可视化结果

生成的 PLY 文件可以用以下工具查看：
- **SuperSplat** (Web): https://superspl.at/
- **PlayCanvas Viewer** (Web): https://playcanvas.com/supersplat/editor/
- **Polycam** (Web): https://poly.cam/tools/gaussian-splatting
- **本地查看器**: SIBR_viewers, gsplat

## 多 GPU 并行测试

如果你的服务器有多张 GPU，可以通过并行测试大幅缩短总时间。

### 并行度建议

| GPU 配置 | 推荐并行度 | 说明 |
|---------|-----------|------|
| 单卡 24GB | 1-2 | 单卡并行可能显存不足 |
| 双 Ada 6000 (48GB) | 4 | 每张卡跑 2 个实例 |
| 四卡 24GB | 4-8 | 根据显存和任务调整 |

### 并行测试示例

```bash
# 查看可用 GPU
nvidia-smi

# 双 Ada 6000 推荐配置（4 并行）
python3 opensplat_param_test.py -p 4

# 如果显存充足，可以尝试更高并行度
python3 opensplat_param_test.py -p 6

# 快速测试并行
python3 quick_test.py -p 4
```

### GPU 分配原理

脚本使用 `CUDA_VISIBLE_DEVICES` 环境变量控制 GPU 分配：
- 并行度为 4 时，任务轮流分配到 GPU 0、1、2、3
- 实际 GPU 数量可能少于并行度（如 2 张卡配 4 并行），任务会在可用 GPU 上轮询

### 并行测试效果

以 22 个测试用例为例：
- **串行模式**: 预估 2-4 小时
- **4 并行模式**: 预估 30-60 分钟（理论加速比 ~4x）

实际加速比取决于：
- GPU 性能
- 显存容量
- 测试用例的迭代次数分布

## 故障排除

### 显存不足
- 增加 `--downscale-factor`
- 减少 `--num-iters`
- 增加 `--refine-every`
- 使用 `--cpu` 模式（慢但不需要 GPU）

### 训练时间过长
- 使用 `quick_test.py` 快速筛选参数
- 减少 `--num-iters`
- 增加 `--downscale-factor`
- 减少 `--sh-degree`

### 质量不佳
- 增加 `--num-iters`
- 减少 `--downscale-factor`（使用更高分辨率）
- 增加 `--sh-degree`
- 降低 `--densify-grad-thresh`（更敏感的分裂）
- 减少 `--refine-every`（更频繁的细化）

## 自定义测试

可以编辑脚本中的 `TEST_CASES` 或 `define_test_cases()` 方法添加自定义测试：

```python
TestCase(
    name="my_test",
    description="我的自定义配置",
    params={
        "num-iters": "20000",
        "sh-degree": "2",
        "ssim-weight": "0.3"
    }
)
```
