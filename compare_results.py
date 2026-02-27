#!/usr/bin/env python3
"""
OpenSplat 结果对比脚本

用于比较不同参数生成的 PLY 文件大小和质量指标
"""

import os
import sys
import glob
from dataclasses import dataclass
from typing import List


@dataclass
class ModelInfo:
    name: str
    file_path: str
    size_mb: float
    num_points: int = 0
    
    def __str__(self):
        return f"{self.name}: {self.size_mb:.2f} MB, {self.num_points:,} points"


def parse_ply_header(file_path: str) -> int:
    """解析 PLY 文件头部获取点数"""
    try:
        with open(file_path, 'rb') as f:
            header = b""
            while True:
                line = f.readline()
                header += line
                if b"end_header" in line:
                    break
                if len(header) > 10000:  # 防止无限循环
                    break
            
            # 解析 element vertex 行
            header_str = header.decode('ascii', errors='ignore')
            for line in header_str.split('\n'):
                if line.startswith('element vertex'):
                    parts = line.split()
                    return int(parts[2])
    except Exception as e:
        pass
    return 0


def analyze_results(output_dir: str = "./output") -> List[ModelInfo]:
    """分析输出目录中的所有 PLY 文件"""
    ply_files = glob.glob(os.path.join(output_dir, "*.ply"))
    
    models = []
    for file_path in sorted(ply_files):
        name = os.path.splitext(os.path.basename(file_path))[0]
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        num_points = parse_ply_header(file_path)
        
        models.append(ModelInfo(name, file_path, size_mb, num_points))
    
    return models


def print_comparison(models: List[ModelInfo]):
    """打印对比结果"""
    print("\n" + "="*70)
    print("OpenSplat 参数对比结果分析")
    print("="*70)
    
    # 分组显示
    groups = {
        "迭代次数": [m for m in models if "iters_" in m.name],
        "图像分辨率": [m for m in models if "scale_" in m.name],
        "球谐函数": [m for m in models if "sh_" in m.name],
        "SSIM权重": [m for m in models if "ssim_" in m.name],
        "细化频率": [m for m in models if "refine_" in m.name],
        "梯度阈值": [m for m in models if "grad_" in m.name],
        "尺寸阈值": [m for m in models if "size_" in m.name],
        "综合配置": [m for m in models if m.name in ["baseline", "fast_preview", "quality"]],
        "其他": [],
    }
    
    # 分配其他
    assigned = set()
    for g in groups.values():
        assigned.update(id(m) for m in g)
    groups["其他"] = [m for m in models if id(m) not in assigned]
    
    for group_name, group_models in groups.items():
        if not group_models:
            continue
        
        print(f"\n【{group_name}】")
        print(f"{'名称':<20} {'文件大小':>12} {'高斯点数':>15} {'效率(MB/万点)':>15}")
        print("-"*70)
        
        for m in sorted(group_models, key=lambda x: x.size_mb):
            efficiency = (m.size_mb / (m.num_points / 10000)) if m.num_points > 0 else 0
            print(f"{m.name:<20} {m.size_mb:>10.2f} MB {m.num_points:>15,} {efficiency:>12.3f}")
    
    # 总体统计
    print("\n" + "="*70)
    print("总体统计")
    print("="*70)
    if models:
        sizes = [m.size_mb for m in models]
        points = [m.num_points for m in models if m.num_points > 0]
        
        print(f"模型数量: {len(models)}")
        print(f"文件大小范围: {min(sizes):.2f} - {max(sizes):.2f} MB (平均: {sum(sizes)/len(sizes):.2f} MB)")
        if points:
            print(f"高斯点数范围: {min(points):,} - {max(points):,} (平均: {sum(points)/len(points):,.0f})")
    
    # 找出最大和最小的模型
    print("\n" + "="*70)
    print("极值分析")
    print("="*70)
    
    if models:
        largest = max(models, key=lambda x: x.size_mb)
        smallest = min(models, key=lambda x: x.size_mb)
        print(f"最大文件: {largest.name} ({largest.size_mb:.2f} MB)")
        print(f"最小文件: {smallest.name} ({smallest.size_mb:.2f} MB)")
        print(f"大小比例: {largest.size_mb / smallest.size_mb:.1f}x")


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./output"
    
    if not os.path.exists(output_dir):
        print(f"错误: 输出目录不存在: {output_dir}")
        print(f"请指定正确的输出目录，例如: python3 compare_results.py ./output")
        sys.exit(1)
    
    models = analyze_results(output_dir)
    
    if not models:
        print(f"警告: 在 {output_dir} 中没有找到 PLY 文件")
        sys.exit(1)
    
    print_comparison(models)


if __name__ == "__main__":
    main()
