## iteration 3000 测试结果汇总
| 测试名称 | 描述 | 参数 | 状态 | GPU | 耗时 | 输出文件 |
|---------|------|------|------|-----|------|----------|
| baseline | 基准配置（3000次迭代，快速测试） | `--num-iters 3000` | ✅ 成功 | 0 | 48.2s | baseline.ply |
| scale_1 | 原始分辨率（高质量，慢速） | `--downscale-factor 1 --num-iters 3000` | ✅ 成功 | 1 | 48.9s | scale_1.ply |
| scale_2 | 1/2 分辨率（平衡） | `--downscale-factor 2 --num-iters 3000` | ✅ 成功 | 0 | 44.9s | scale_2.ply |
| scale_4 | 1/4 分辨率（快速预览） | `--downscale-factor 4 --num-iters 3000` | ✅ 成功 | 1 | 44.5s | scale_4.ply |
| sh_1 | SH Degree 1（基础光照，最快） | `--sh-degree 1 --num-iters 3000` | ✅ 成功 | 0 | 48.4s | sh_1.ply |
| sh_2 | SH Degree 2（中等光照） | `--sh-degree 2 --num-iters 3000` | ✅ 成功 | 1 | 49.5s | sh_2.ply |
| sh_3 | SH Degree 3（默认，完整光照） | `--sh-degree 3 --num-iters 3000` | ✅ 成功 | 0 | 48.0s | sh_3.ply |
| ssim_0 | SSIM权重0（纯L1损失） | `--ssim-weight 0 --num-iters 3000` | ✅ 成功 | 1 | 47.5s | ssim_0.ply |
| ssim_0.5 | SSIM权重0.5（更强调结构相似性） | `--ssim-weight 0.5 --num-iters 3000` | ✅ 成功 | 1 | 39.2s | ssim_0.5.ply |
| ssim_0.2 | SSIM权重0.2（默认平衡） | `--ssim-weight 0.2 --num-iters 3000` | ✅ 成功 | 0 | 46.7s | ssim_0.2.ply |
| refine_50 | 每50步细化（更频繁，更多高斯） | `--refine-every 50 --num-iters 3000` | ✅ 成功 | 0 | 49.7s | refine_50.ply |
| refine_100 | 每100步细化（默认） | `--refine-every 100 --num-iters 3000` | ✅ 成功 | 1 | 44.8s | refine_100.ply |
| refine_200 | 每200步细化（更稀疏，更少高斯） | `--refine-every 200 --num-iters 3000` | ✅ 成功 | 0 | 47.5s | refine_200.ply |
| grad_0.0001 | 梯度阈值0.0001（更敏感，更多分裂） | `--densify-grad-thresh 0.0001 --num-iters 3000` | ✅ 成功 | 1 | 50.8s | grad_0.0001.ply |
| grad_0.0002 | 梯度阈值0.0002（默认） | `--densify-grad-thresh 0.0002 --num-iters 3000` | ✅ 成功 | 0 | 48.9s | grad_0.0002.ply |
| grad_0.0004 | 梯度阈值0.0004（较不敏感，较少分裂） | `--densify-grad-thresh 0.0004 --num-iters 3000` | ✅ 成功 | 1 | 47.7s | grad_0.0004.ply |
| size_0.01 | 尺寸阈值0.01（默认） | `--densify-size-thresh 0.01 --num-iters 3000` | ✅ 成功 | 1 | 30.0s | size_0.01.ply |
| size_0.005 | 尺寸阈值0.005（更多复制） | `--densify-size-thresh 0.005 --num-iters 3000` | ✅ 成功 | 0 | 47.3s | size_0.005.ply |
| fast_preview | 快速预览配置（牺牲质量换取速度） | `--downscale-factor 4 --num-iters 1000 --sh-degree 1 --refine-every 200` | ✅ 成功 | 1 | 17.6s | fast_preview.ply |
| size_0.02 | 尺寸阈值0.02（更多分裂） | `--densify-size-thresh 0.02 --num-iters 3000` | ✅ 成功 | 0 | 47.7s | size_0.02.ply |

---

## iteration 1000 测试结果汇总
| 测试名称 | 描述 | 参数 | 状态 | GPU | 耗时 | 输出文件 |
|---------|------|------|------|-----|------|----------|
| baseline | 基准配置（3000次迭代，快速测试） | `--num-iters 1000` | ✅ 成功 | 0 | 19.5s | baseline.ply |
| scale_1 | 原始分辨率（高质量，慢速） | `--downscale-factor 1 --num-iters 1000` | ✅ 成功 | 1 | 19.6s | scale_1.ply |
| scale_4 | 1/4 分辨率（快速预览） | `--downscale-factor 4 --num-iters 1000` | ✅ 成功 | 1 | 16.9s | scale_4.ply |
| scale_2 | 1/2 分辨率（平衡） | `--downscale-factor 2 --num-iters 1000` | ✅ 成功 | 0 | 17.8s | scale_2.ply |
| sh_1 | SH Degree 1（基础光照，最快） | `--sh-degree 1 --num-iters 1000` | ✅ 成功 | 0 | 18.9s | sh_1.ply |
| sh_2 | SH Degree 2（中等光照） | `--sh-degree 2 --num-iters 1000` | ✅ 成功 | 1 | 19.5s | sh_2.ply |
| sh_3 | SH Degree 3（默认，完整光照） | `--sh-degree 3 --num-iters 1000` | ✅ 成功 | 0 | 19.0s | sh_3.ply |
| ssim_0 | SSIM权重0（纯L1损失） | `--ssim-weight 0 --num-iters 1000` | ✅ 成功 | 1 | 19.4s | ssim_0.ply |
| ssim_0.2 | SSIM权重0.2（默认平衡） | `--ssim-weight 0.2 --num-iters 1000` | ✅ 成功 | 0 | 18.6s | ssim_0.2.ply |
| ssim_0.5 | SSIM权重0.5（更强调结构相似性） | `--ssim-weight 0.5 --num-iters 1000` | ✅ 成功 | 1 | 19.2s | ssim_0.5.ply |
| refine_50 | 每50步细化（更频繁，更多高斯） | `--refine-every 50 --num-iters 1000` | ✅ 成功 | 0 | 18.6s | refine_50.ply |
| refine_100 | 每100步细化（默认） | `--refine-every 100 --num-iters 1000` | ✅ 成功 | 1 | 18.9s | refine_100.ply |
| refine_200 | 每200步细化（更稀疏，更少高斯） | `--refine-every 200 --num-iters 1000` | ✅ 成功 | 0 | 18.9s | refine_200.ply |
| grad_0.0001 | 梯度阈值0.0001（更敏感，更多分裂） | `--densify-grad-thresh 0.0001 --num-iters 1000` | ✅ 成功 | 1 | 19.0s | grad_0.0001.ply |
| grad_0.0002 | 梯度阈值0.0002（默认） | `--densify-grad-thresh 0.0002 --num-iters 1000` | ✅ 成功 | 0 | 18.8s | grad_0.0002.ply |
| grad_0.0004 | 梯度阈值0.0004（较不敏感，较少分裂） | `--densify-grad-thresh 0.0004 --num-iters 1000` | ✅ 成功 | 1 | 18.3s | grad_0.0004.ply |
| size_0.005 | 尺寸阈值0.005（更多复制） | `--densify-size-thresh 0.005 --num-iters 1000` | ✅ 成功 | 0 | 19.1s | size_0.005.ply |
| size_0.01 | 尺寸阈值0.01（默认） | `--densify-size-thresh 0.01 --num-iters 1000` | ✅ 成功 | 1 | 18.6s | size_0.01.ply |
| size_0.02 | 尺寸阈值0.02（更多分裂） | `--densify-size-thresh 0.02 --num-iters 1000` | ✅ 成功 | 0 | 18.8s | size_0.02.ply |
| fast_preview | 快速预览配置（牺牲质量换取速度） | `--downscale-factor 4 --num-iters 1000 --sh-degree 1 --refine-every 200` | ✅ 成功 | 1 | 17.4s | fast_preview.ply |

---