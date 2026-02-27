#!/usr/bin/env python3
"""
OpenSplat 参数对比测试脚本（支持多 GPU 并行）

该脚本用于自动化测试 opensplat 不同参数配置下的建模效果。
使用 banana 数据集作为测试基准。

使用方法:
    python3 opensplat_param_test.py                    # 串行运行（默认）
    python3 opensplat_param_test.py -p 4               # 并行运行 4 个测试
    python3 opensplat_param_test.py --parallel 2       # 并行运行 2 个测试
    python3 opensplat_param_test.py -p 4 -o ./results  # 指定输出目录

输出:
    - 在 output/ 目录下生成各参数组合的建模结果
    - 生成测试报告 report.md
"""

import os
import sys
import json
import time
import subprocess
import argparse
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class TestCase:
    """单个测试用例配置"""
    name: str                    # 测试名称
    description: str             # 测试描述
    params: Dict[str, str]       # 参数字典
    
    def get_param_str(self) -> str:
        """生成命令行参数字符串"""
        return " ".join([f"--{k} {v}" if not k.startswith('-') else f"{k} {v}" 
                        for k, v in self.params.items()])


@dataclass
class TestResult:
    """测试结果"""
    test_case: TestCase
    success: bool
    duration: float
    output_file: str
    gpu_id: int
    error_msg: Optional[str] = None


class OpenSplatTester:
    """OpenSplat 参数测试器（支持多 GPU 并行）"""
    
    def __init__(self, 
                 opensplat_path: str = "./opensplat",
                 data_path: str = "./banana",
                 output_dir: str = "./output",
                 max_workers: int = 1,
                 timeout: int = 3600):
        self.opensplat_path = opensplat_path
        self.data_path = data_path
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.timeout = timeout
        self._print_lock = threading.Lock()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
    def _safe_print(self, *args, **kwargs):
        """线程安全的打印"""
        with self._print_lock:
            print(*args, **kwargs)
        
    def run_single_test(self, test_case: TestCase, gpu_id: int = 0) -> TestResult:
        """运行单个测试用例"""
        output_file = os.path.join(self.output_dir, f"{test_case.name}.ply")
        
        # 构建命令
        cmd = [
            self.opensplat_path,
            "-o", output_file,
            *test_case.get_param_str().split(),
            self.data_path
        ]
        
        # 设置环境变量，指定使用哪个 GPU
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        
        self._safe_print(f"\n{'='*60}")
        self._safe_print(f"[GPU {gpu_id}] 开始测试: {test_case.name}")
        self._safe_print(f"描述: {test_case.description}")
        self._safe_print(f"命令: CUDA_VISIBLE_DEVICES={gpu_id} {' '.join(cmd)}")
        self._safe_print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,  # 使用自定义超时时间
                env=env
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # 获取输出文件大小
                file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                self._safe_print(f"✅ [GPU {gpu_id}] {test_case.name} 成功! 耗时: {duration:.1f}s, 文件: {file_size:.2f} MB")
                return TestResult(test_case, True, duration, output_file, gpu_id)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                self._safe_print(f"❌ [GPU {gpu_id}] {test_case.name} 失败! 错误: {error_msg[:200]}")
                return TestResult(test_case, False, duration, output_file, gpu_id, error_msg)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self._safe_print(f"⏱️ [GPU {gpu_id}] {test_case.name} 超时!")
            return TestResult(test_case, False, duration, output_file, gpu_id, "Timeout")
        except Exception as e:
            duration = time.time() - start_time
            self._safe_print(f"❌ [GPU {gpu_id}] {test_case.name} 异常! {str(e)}")
            return TestResult(test_case, False, duration, output_file, gpu_id, str(e))
    
    def define_test_cases(self) -> List[TestCase]:
        """定义所有测试用例"""
        test_cases = []
        
        # ============== 基准测试 ==============
        test_cases.append(TestCase(
            name="baseline",
            description="基准配置（3000次迭代，快速测试）",
            params={"num-iters": "1000"}
        ))
        
        # ============== 1. 迭代次数测试 ==============
        # test_cases.extend([
        #     TestCase(
        #         name="iters_10000",
        #         description="迭代10000步（快速预览）",
        #         params={"num-iters": "10000"}
        #     ),
        #     TestCase(
        #         name="iters_30000",
        #         description="迭代30000步（默认）",
        #         params={"num-iters": "30000"}
        #     ),
        #     TestCase(
        #         name="iters_50000",
        #         description="迭代50000步（更高质量）",
        #         params={"num-iters": "50000"}
        #     ),
        # ])
        
        # ============== 2. 图像分辨率测试 ==============
        test_cases.extend([
            TestCase(
                name="scale_1",
                description="原始分辨率（高质量，慢速）",
                params={"downscale-factor": "1", "num-iters": "1000"}
            ),
            TestCase(
                name="scale_2",
                description="1/2 分辨率（平衡）",
                params={"downscale-factor": "2", "num-iters": "1000"}
            ),
            TestCase(
                name="scale_4",
                description="1/4 分辨率（快速预览）",
                params={"downscale-factor": "4", "num-iters": "1000"}
            ),
        ])
        
        # ============== 3. 球谐函数阶数测试 ==============
        test_cases.extend([
            TestCase(
                name="sh_1",
                description="SH Degree 1（基础光照，最快）",
                params={"sh-degree": "1", "num-iters": "1000"}
            ),
            TestCase(
                name="sh_2",
                description="SH Degree 2（中等光照）",
                params={"sh-degree": "2", "num-iters": "1000"}
            ),
            TestCase(
                name="sh_3",
                description="SH Degree 3（默认，完整光照）",
                params={"sh-degree": "3", "num-iters": "1000"}
            ),
        ])
        
        # ============== 4. SSIM 权重测试 ==============
        test_cases.extend([
            TestCase(
                name="ssim_0",
                description="SSIM权重0（纯L1损失）",
                params={"ssim-weight": "0", "num-iters": "1000"}
            ),
            TestCase(
                name="ssim_0.2",
                description="SSIM权重0.2（默认平衡）",
                params={"ssim-weight": "0.2", "num-iters": "1000"}
            ),
            TestCase(
                name="ssim_0.5",
                description="SSIM权重0.5（更强调结构相似性）",
                params={"ssim-weight": "0.5", "num-iters": "1000"}
            ),
        ])
        
        # ============== 5. 细化频率测试 ==============
        test_cases.extend([
            TestCase(
                name="refine_50",
                description="每50步细化（更频繁，更多高斯）",
                params={"refine-every": "50", "num-iters": "1000"}
            ),
            TestCase(
                name="refine_100",
                description="每100步细化（默认）",
                params={"refine-every": "100", "num-iters": "1000"}
            ),
            TestCase(
                name="refine_200",
                description="每200步细化（更稀疏，更少高斯）",
                params={"refine-every": "200", "num-iters": "1000"}
            ),
        ])
        
        # ============== 6. 梯度阈值测试 ==============
        test_cases.extend([
            TestCase(
                name="grad_0.0001",
                description="梯度阈值0.0001（更敏感，更多分裂）",
                params={"densify-grad-thresh": "0.0001", "num-iters": "1000"}
            ),
            TestCase(
                name="grad_0.0002",
                description="梯度阈值0.0002（默认）",
                params={"densify-grad-thresh": "0.0002", "num-iters": "1000"}
            ),
            TestCase(
                name="grad_0.0004",
                description="梯度阈值0.0004（较不敏感，较少分裂）",
                params={"densify-grad-thresh": "0.0004", "num-iters": "1000"}
            ),
        ])
        
        # ============== 7. 尺寸阈值测试 ==============
        test_cases.extend([
            TestCase(
                name="size_0.005",
                description="尺寸阈值0.005（更多复制）",
                params={"densify-size-thresh": "0.005", "num-iters": "1000"}
            ),
            TestCase(
                name="size_0.01",
                description="尺寸阈值0.01（默认）",
                params={"densify-size-thresh": "0.01", "num-iters": "1000"}
            ),
            TestCase(
                name="size_0.02",
                description="尺寸阈值0.02（更多分裂）",
                params={"densify-size-thresh": "0.02", "num-iters": "1000"}
            ),
        ])
        
        # ============== 8. 综合优化配置 ==============
        test_cases.extend([
            TestCase(
                name="fast_preview",
                description="快速预览配置（牺牲质量换取速度）",
                params={
                    "downscale-factor": "4",
                    "num-iters": "1000",
                    "sh-degree": "1",
                    "refine-every": "200"
                }
            ),
            # TestCase(
            #     name="quality",
            #     description="高质量配置（牺牲速度换取质量）",
            #     params={
            #         "downscale-factor": "1",
            #         "num-iters": "50000",
            #         "sh-degree": "3",
            #         "refine-every": "50",
            #         "densify-grad-thresh": "0.0001"
            #     }
            # ),
        ])
        
        return test_cases
    
    def run_all_tests(self, test_cases: Optional[List[TestCase]] = None) -> List[TestResult]:
        """运行所有测试（支持并行）"""
        if test_cases is None:
            test_cases = self.define_test_cases()
        
        print(f"\n{'#'*70}")
        print(f"# OpenSplat 参数对比测试")
        print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# 测试数量: {len(test_cases)}")
        print(f"# 并行度: {self.max_workers}")
        print(f"# 输出目录: {self.output_dir}")
        print(f"# 数据路径: {self.data_path}")
        print(f"{'#'*70}\n")
        
        results = []
        
        if self.max_workers <= 1:
            # 串行执行
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n[进度 {i}/{len(test_cases)}]", end="")
                result = self.run_single_test(test_case, gpu_id=0)
                results.append(result)
        else:
            # 并行执行
            # 轮询分配 GPU
            gpu_assignments = [i % self.max_workers for i in range(len(test_cases))]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_test = {
                    executor.submit(self.run_single_test, test_case, gpu_id): (test_case, i)
                    for i, (test_case, gpu_id) in enumerate(zip(test_cases, gpu_assignments))
                }
                
                # 收集结果
                completed = 0
                for future in as_completed(future_to_test):
                    test_case, index = future_to_test[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        self._safe_print(f"\n[完成 {completed}/{len(test_cases)}] {test_case.name}")
                    except Exception as e:
                        completed += 1
                        self._safe_print(f"\n[完成 {completed}/{len(test_cases)}] {test_case.name} - 异常: {e}")
                        # 创建一个失败的测试结果
                        results.append(TestResult(test_case, False, 0, "", gpu_assignments[index], str(e)))
        
        return results
    
    def generate_report(self, results: List[TestResult]) -> str:
        """生成测试报告"""
        report_lines = [
            "# OpenSplat 参数对比测试报告\n",
            f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**数据集:** banana\n",
            f"**测试总数:** {len(results)}\n",
            f"**并行度:** {self.max_workers}\n",
            "\n---\n",
            "## 测试结果汇总\n",
            "| 测试名称 | 描述 | 参数 | 状态 | GPU | 耗时 | 输出文件 |\n",
            "|---------|------|------|------|-----|------|----------|\n",
        ]
        
        for r in results:
            status = "✅ 成功" if r.success else "❌ 失败"
            params = r.test_case.get_param_str() if r.test_case.params else "默认"
            output_name = os.path.basename(r.output_file)
            
            # 转义表格中的特殊字符
            params = params.replace("|", "\\|").replace("\n", " ")
            desc = r.test_case.description.replace("|", "\\|").replace("\n", " ")
            
            report_lines.append(
                f"| {r.test_case.name} | {desc} | `{params}` | {status} | {r.gpu_id} | {r.duration:.1f}s | {output_name} |\n"
            )
        
        # 失败详情
        failed_results = [r for r in results if not r.success]
        if failed_results:
            report_lines.extend([
                "\n---\n",
                "## 失败的测试\n",
            ])
            for r in failed_results:
                report_lines.extend([
                    f"### {r.test_case.name}\n",
                    f"- **错误信息:** {r.error_msg[:500] if r.error_msg else 'Unknown'}\n"
                ])
        
        # 参数说明
        report_lines.extend([
            "\n---\n",
            "## 参数说明与影响分析\n",
            "\n### 1. 迭代次数 (`--num-iters`)\n",
            "- **作用:** 控制训练的总步数\n",
            "- **影响:** 更多迭代通常带来更好的收敛和质量，但增加训练时间\n",
            "- **建议:** 快速预览用 5000-10000，最终渲染用 30000-50000\n",
            "\n### 2. 图像分辨率 (`--downscale-factor`)\n",
            "- **作用:** 输入图像的缩放因子\n",
            "- **影响:** 更高分辨率保留更多细节但显著增加计算量和显存需求\n",
            "- **建议:** 预览用 2-4，最终渲染用 1\n",
            "\n### 3. 球谐函数阶数 (`--sh-degree`)\n",
            "- **作用:** 控制视角相关光照的复杂度\n",
            "- **影响:** 更高阶数支持更复杂的光照效果（镜面反射、次表面散射等）\n",
            "- **建议:** 简单场景用 1-2，复杂光照用 3\n",
            "\n### 4. SSIM权重 (`--ssim-weight`)\n",
            "- **作用:** 平衡 L1 损失和 SSIM 结构相似性损失\n",
            "- **影响:** 更高的 SSIM 权重强调结构保真度，但可能损失部分细节\n",
            "- **建议:** 一般保持默认 0.2，追求结构清晰可提高到 0.3-0.5\n",
            "\n### 5. 细化频率 (`--refine-every`)\n",
            "- **作用:** 控制高斯分裂/复制/修剪的频率\n",
            "- **影响:** 更频繁的细化产生更多高斯点，提高细节但增加显存\n",
            "- **建议:** 默认 100，追求细节用 50，快速训练用 200\n",
            "\n### 6. 梯度阈值 (`--densify-grad-thresh`)\n",
            "- **作用:** 触发高斯分裂/复制的梯度阈值\n",
            "- **影响:** 更低的阈值使更多区域触发细化，增加高斯数量\n",
            "- **建议:** 细节丰富的场景用 0.0001，简单场景用 0.0004\n",
            "\n### 7. 尺寸阈值 (`--densify-size-thresh`)\n",
            "- **作用:** 区分复制和分裂的尺寸边界\n",
            "- **影响:** 小高斯复制，大高斯分裂\n",
            "- **建议:** 一般保持默认 0.01\n",
            "\n---\n",
            "## 快速参考配置\n",
            "\n### 快速预览\n",
            "```bash\n",
            "./opensplat -o preview.ply --downscale-factor 4 --num-iters 5000 --sh-degree 1 banana/\n",
            "```\n",
            "\n### 平衡配置\n",
            "```bash\n",
            "./opensplat -o balanced.ply --downscale-factor 2 --num-iters 30000 banana/\n",
            "```\n",
            "\n### 高质量配置\n",
            "```bash\n",
            "./opensplat -o quality.ply --downscale-factor 1 --num-iters 50000 --sh-degree 3 --refine-every 50 banana/\n",
            "```\n",
            "\n### 并行测试示例\n",
            "```bash\n",
            "# 使用 4 个并行进程（适合双 Ada 6000）\n",
            "python3 opensplat_param_test.py -p 4\n",
            "\n",
            "# 使用 2 个并行进程（适合单卡）\n",
            "python3 opensplat_param_test.py -p 2\n",
            "```\n",
        ])
        
        return "".join(report_lines)
    
    def save_report(self, results: List[TestResult], filename: str = "report.md"):
        """保存测试报告"""
        report = self.generate_report(results)
        report_path = os.path.join(self.output_dir, filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 测试报告已保存: {report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OpenSplat 参数对比测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 opensplat_param_test.py              # 串行运行（默认）
  python3 opensplat_param_test.py -p 4         # 并行运行 4 个测试
  python3 opensplat_param_test.py -p 2 -o ./results  # 指定输出目录
  python3 opensplat_param_test.py --parallel 4 --yes # 自动确认，无需交互
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
        default="./output",
        help="输出目录（默认 ./output）"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="自动确认，无需交互"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="单个测试超时时间（秒，默认 3600=1小时）"
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="只运行指定的测试名称（逗号分隔，如: iters_50000,quality）"
    )
    
    args = parser.parse_args()
    
    # 检查可执行文件和数据是否存在
    if not os.path.exists("./opensplat"):
        print("错误: 找不到 opensplat 可执行文件")
        sys.exit(1)
    
    if not os.path.exists("./banana"):
        print("错误: 找不到 banana 数据目录")
        sys.exit(1)
    
    # 创建测试器
    tester = OpenSplatTester(
        opensplat_path="./opensplat",
        data_path="./banana",
        output_dir=args.output,
        max_workers=args.parallel,
        timeout=args.timeout
    )
    
    # 获取测试用例（可以自定义）
    all_test_cases = tester.define_test_cases()
    
    # 如果只运行指定测试
    if args.only:
        only_names = [n.strip() for n in args.only.split(",")]
        test_cases = [tc for tc in all_test_cases if tc.name in only_names]
        if not test_cases:
            print(f"错误: 找不到指定的测试: {args.only}")
            print(f"可用测试: {', '.join(tc.name for tc in all_test_cases)}")
            sys.exit(1)
        print(f"\n⚠️ 只运行指定测试: {', '.join(tc.name for tc in test_cases)}")
    else:
        test_cases = all_test_cases
    
    # 显示测试计划
    print("\n" + "="*70)
    print("测试计划:")
    print("="*70)
    print(f"并行度: {args.parallel}")
    print(f"输出目录: {args.output}")
    print("-"*70)
    for i, tc in enumerate(test_cases, 1):
        params = tc.get_param_str() if tc.params else "(默认参数)"
        print(f"{i:2d}. {tc.name:20s} - {tc.description}")
        print(f"    参数: {params}")
    print("="*70)
    
    # 询问是否继续
    if not args.yes:
        response = input(f"\n共 {len(test_cases)} 个测试，并行度 {args.parallel}。是否开始测试? [Y/n]: ").strip().lower()
        if response and response not in ('y', 'yes'):
            print("已取消测试")
            sys.exit(0)
    
    # 运行测试
    start_time = time.time()
    results = tester.run_all_tests(test_cases)
    total_duration = time.time() - start_time
    
    # 生成报告
    tester.save_report(results)
    
    # 打印汇总
    success_count = sum(1 for r in results if r.success)
    print(f"\n{'#'*70}")
    print(f"# 测试完成!")
    print(f"# 成功: {success_count}/{len(results)}")
    print(f"# 串行预估耗时: {sum(r.duration for r in results):.1f}s")
    print(f"# 实际总耗时: {total_duration:.1f}s")
    if total_duration < sum(r.duration for r in results):
        print(f"# 加速比: {sum(r.duration for r in results) / total_duration:.1f}x")
    print(f"{'#'*70}")


if __name__ == "__main__":
    main()
