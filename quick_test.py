#!/usr/bin/env python3
"""
OpenSplat 快速测试脚本（支持多 GPU 并行）

用于快速验证参数效果，只测试 7 个核心配置

使用方法:
    python3 quick_test.py              # 串行运行
    python3 quick_test.py -p 4         # 并行运行 4 个测试
    python3 quick_test.py -p 2 -o ./quick_results  # 指定输出目录
"""

import os
import sys
import subprocess
import time
import argparse
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_DIR = "./output_quick"

TEST_CASES = [
    ("baseline", "默认参数基准", [], 0),
    ("fast", "快速预览 (scale=4, iters=5000)", ["--downscale-factor", "4", "--num-iters", "5000"], 0),
    ("high_res", "高分辨率 (scale=1, iters=15000)", ["--downscale-factor", "1", "--num-iters", "15000"], 0),
    ("sh1", "简单光照 (sh-degree=1)", ["--sh-degree", "1", "--num-iters", "10000"], 0),
    ("ssim_high", "强调结构 (ssim-weight=0.5)", ["--ssim-weight", "0.5", "--num-iters", "10000"], 0),
    ("frequent_refine", "频繁细化 (refine-every=50)", ["--refine-every", "50", "--num-iters", "10000"], 0),
    ("sensitive_grad", "敏感梯度 (grad-thresh=0.0001)", ["--densify-grad-thresh", "0.0001", "--num-iters", "10000"], 0),
]

_print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    """线程安全的打印"""
    with _print_lock:
        print(*args, **kwargs)


def run_test(name, desc, params, gpu_id=0):
    output_file = os.path.join(OUTPUT_DIR, f"{name}.ply")
    cmd = ["./opensplat", "-o", output_file] + params + ["./banana"]
    
    # 设置环境变量，指定使用哪个 GPU
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    safe_print(f"\n{'='*60}")
    safe_print(f"[GPU {gpu_id}] 测试: {name}")
    safe_print(f"描述: {desc}")
    safe_print(f"命令: CUDA_VISIBLE_DEVICES={gpu_id} {' '.join(cmd)}")
    safe_print(f"{'='*60}")
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duration = time.time() - start
    
    if result.returncode == 0:
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        safe_print(f"✅ [GPU {gpu_id}] {name} 成功! 耗时: {duration:.1f}s, 文件: {size_mb:.2f}MB")
        return (name, desc, True, duration, size_mb, gpu_id)
    else:
        error = result.stderr[:200] if result.stderr else "Unknown"
        safe_print(f"❌ [GPU {gpu_id}] {name} 失败: {error}")
        return (name, desc, False, duration, 0, gpu_id)


def run_parallel(max_workers=4):
    """并行运行测试"""
    # 轮询分配 GPU
    gpu_assignments = [i % max_workers for i in range(len(TEST_CASES))]
    
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_test = {
            executor.submit(run_test, name, desc, params, gpu_id): (name, i)
            for i, ((name, desc, params, _), gpu_id) in enumerate(zip(TEST_CASES, gpu_assignments))
        }
        
        for future in as_completed(future_to_test):
            name, index = future_to_test[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                safe_print(f"\n[完成 {completed}/{len(TEST_CASES)}] {name}")
            except Exception as e:
                completed += 1
                safe_print(f"\n[完成 {completed}/{len(TEST_CASES)}] {name} - 异常: {e}")
                results.append((name, TEST_CASES[index][1], False, 0, 0, gpu_assignments[index]))
    
    return results


def run_serial():
    """串行运行测试"""
    results = []
    for i, (name, desc, params, _) in enumerate(TEST_CASES, 1):
        print(f"\n[进度 {i}/{len(TEST_CASES)}]")
        result = run_test(name, desc, params, gpu_id=0)
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="OpenSplat 快速测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 quick_test.py              # 串行运行
  python3 quick_test.py -p 4         # 并行运行 4 个测试
  python3 quick_test.py -p 2 -o ./results  # 指定输出目录
        """
    )
    parser.add_argument(
        "-p", "--parallel",
        type=int,
        default=1,
        help="并行测试数量（根据 GPU 数量和显存设置，默认 1）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output_quick",
        help="输出目录（默认 ./output_quick）"
    )
    
    args = parser.parse_args()
    
    # 更新全局输出目录
    global OUTPUT_DIR
    OUTPUT_DIR = args.output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("="*70)
    print("OpenSplat 快速参数测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"并行度: {args.parallel}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("="*70)
    
    start_time = time.time()
    
    if args.parallel > 1:
        results = run_parallel(args.parallel)
    else:
        results = run_serial()
    
    total_duration = time.time() - start_time
    
    # 打印汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    print(f"{'名称':<15} {'描述':<30} {'GPU':<5} {'状态':<8} {'耗时':<10} {'大小':<10}")
    print("-"*70)
    for name, desc, success, duration, size, gpu_id in results:
        status = "✅" if success else "❌"
        print(f"{name:<15} {desc:<30} {gpu_id:<5} {status:<8} {duration:>6.1f}s   {size:>6.2f}MB")
    
    total_time = sum(r[3] for r in results)
    success_count = sum(1 for r in results if r[2])
    print("-"*70)
    print(f"总计: {success_count}/{len(results)} 成功")
    print(f"串行预估耗时: {total_time:.1f}s")
    print(f"实际总耗时: {total_duration:.1f}s")
    if args.parallel > 1 and total_duration < total_time:
        print(f"加速比: {total_time / total_duration:.1f}x")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
