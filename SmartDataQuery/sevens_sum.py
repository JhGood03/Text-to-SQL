"""
计算 1-100 之间（包含 1，不包含 100）所有能被 7 整除
或者包含数字 7 的数之和。
"""


def collect_special_numbers(start: int, end: int) -> list[int]:
    """收集区间 [start, end) 内能被 7 整除或包含数字 7 的所有整数。"""
    result = []
    for n in range(start, end):
        if n % 7 == 0 or '7' in str(n):
            result.append(n)
    return result


def sum_special_numbers(start: int, end: int) -> tuple[int, list[int]]:
    """返回 (总和, 符合要求的数列表)。"""
    numbers = collect_special_numbers(start, end)
    return sum(numbers), numbers


def main() -> None:
    total, numbers = sum_special_numbers(1, 100)
    print("1-100 之间（包含 1，不包含 100）符合要求的数有：")
    print(numbers)
    print(f"符合要求的数共有 {len(numbers)} 个")
    print(f"它们的总和为：{total}")


if __name__ == "__main__":
    main()
