"""
==========================================================
  Budget Planning Agent – Test Case Validator
  Dùng để kiểm tra tính đúng đắn của 8 test case đã thiết kế
  đối chiếu với mock data gốc.
==========================================================
  Usage:
      python validate_test_cases.py
      python validate_test_cases.py --verbose
      python validate_test_cases.py --tc TC003
==========================================================
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Any

# ── ANSI Colors ────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── Paths ──────────────────────────────────────────────────
MOCK_DATA_FILE = Path("products_mockdata.json")
TEST_CASE_FILE = Path("budget_agent_test_cases.json")

# ── Helpers ────────────────────────────────────────────────

def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def price_after_discount(product: dict) -> float:
    return round(product["price"] * (1 - product["discount_percent"] / 100), 2)

def fmt_vnd(amount: float) -> str:
    return f"{amount:,.0f} VNĐ"

def build_product_map(products: list) -> dict:
    return {p["id"]: p for p in products}

def get_in_stock(products: list, category: str = None) -> list:
    result = [p for p in products if p["stock"] > 0]
    if category:
        result = [p for p in result if p["category"] == category]
    return result

def find_best_combo(products: list, budget: float, categories: list, optimize_by: str = "performance_score"):
    """Brute-force tìm tổ hợp tối ưu trong ngân sách."""
    by_cat = {}
    for cat in categories:
        by_cat[cat] = sorted(get_in_stock(products, cat), key=lambda x: x[optimize_by], reverse=True)

    best = None
    best_score = -1

    def recurse(cats_remaining, chosen, cost_so_far):
        nonlocal best, best_score
        if not cats_remaining:
            total_score = sum(p[optimize_by] for p in chosen.values())
            if total_score > best_score:
                best_score = total_score
                best = (dict(chosen), cost_so_far, total_score)
            return
        cat = cats_remaining[0]
        for p in by_cat[cat]:
            c = price_after_discount(p)
            if cost_so_far + c <= budget:
                chosen[cat] = p
                recurse(cats_remaining[1:], chosen, cost_so_far + c)
                del chosen[cat]

    recurse(categories, {}, 0)
    return best


# ══════════════════════════════════════════════════════════
#  ValidationResult
# ══════════════════════════════════════════════════════════

class ValidationResult:
    def __init__(self, tc_id: str):
        self.tc_id = tc_id
        self.checks = []  # (label, passed, detail)

    def add(self, label: str, passed: bool, detail: str = ""):
        self.checks.append((label, passed, detail))

    @property
    def passed(self):
        return all(c[1] for c in self.checks)

    @property
    def n_pass(self):
        return sum(1 for c in self.checks if c[1])

    @property
    def n_total(self):
        return len(self.checks)


# ══════════════════════════════════════════════════════════
#  Individual Validators
# ══════════════════════════════════════════════════════════

def validate_TC001(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]

    laptops_in_stock = get_in_stock(products, "laptop")
    cheapest = min(price_after_discount(p) for p in laptops_in_stock)
    r.add("Laptop rẻ nhất sau giảm > 5 triệu (budget)",
          cheapest > budget,
          f"Laptop rẻ nhất: {fmt_vnd(cheapest)} > {fmt_vnd(budget)}")

    r.add("expected_output.feasible = False",
          tc["expected_output"]["feasible"] is False,
          f"feasible = {tc['expected_output']['feasible']}")

    r.add("Có suggestion / partial plan",
          bool(tc["expected_output"].get("suggestion")),
          tc["expected_output"].get("suggestion", "(trống)")[:80])

    cats = tc.get("required_categories", [])
    r.add("required_categories đủ 3 loại",
          set(cats) == {"laptop", "mouse", "keyboard"}, str(cats))

    # Ground-truth: thử combo rẻ nhất có laptop
    combo = find_best_combo(products, budget, ["laptop", "mouse", "keyboard"])
    r.add("Ground-truth: không tồn tại combo laptop+mouse+keyboard <= 5 triệu",
          combo is None,
          "Không tìm được combo khả thi" if combo is None else f"Combo tồn tại! {combo[1]:,.0f}")
    return r


def validate_TC002(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    combo = tc["expected_output"]["recommended_combo"]
    prod_map = build_product_map(products)

    oos = [p["id"] for p in combo if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Tất cả sản phẩm đề xuất còn hàng", len(oos) == 0,
          f"Hết hàng: {oos}" if oos else "OK")

    price_errors = []
    for p in combo:
        if p["id"] not in prod_map: continue
        actual = price_after_discount(prod_map[p["id"]])
        diff = abs(p["price_after_discount"] - actual)
        if diff >= 10:
            price_errors.append(f"{p['id']}: stated={fmt_vnd(p['price_after_discount'])}, actual={fmt_vnd(actual)}")
    r.add("Giá sau giảm tính đúng (sai số < 10 VNĐ)", len(price_errors) == 0,
          " | ".join(price_errors) if price_errors else "OK")

    total = tc["expected_output"]["total_cost"]
    r.add("total_cost <= budget", total <= budget, f"{fmt_vnd(total)} <= {fmt_vnd(budget)}")

    calc_total = sum(p["price_after_discount"] for p in combo)
    r.add("total_cost = sum(price_after_discount)",
          abs(calc_total - total) < 50, f"calc={fmt_vnd(calc_total)}, stated={fmt_vnd(total)}")

    calc_score = sum(prod_map[p["id"]]["performance_score"] for p in combo if p["id"] in prod_map)
    stated_score = tc["expected_output"]["total_performance_score"]
    r.add("total_performance_score đúng", calc_score == stated_score,
          f"calc={calc_score}, stated={stated_score}")

    stated_remaining = tc["expected_output"]["remaining_budget"]
    r.add("remaining_budget = budget - total_cost",
          abs(stated_remaining - (budget - total)) < 50,
          f"calc={fmt_vnd(budget - total)}, stated={fmt_vnd(stated_remaining)}")

    best = find_best_combo(products, budget, ["mouse", "keyboard"])
    if best:
        _, _, best_score = best
        r.add("Combo đề xuất đạt score tối ưu",
              stated_score >= best_score,
              f"score đề xuất={stated_score}, score tốt nhất={best_score}")
    return r


def validate_TC003(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    combo = tc["expected_output"]["recommended_combo"]
    prod_map = build_product_map(products)

    r.add("feasible = True", tc["expected_output"]["feasible"] is True)

    cats_in_combo = {prod_map[p["id"]]["category"] for p in combo if p["id"] in prod_map}
    r.add("Combo có đủ laptop + mouse + keyboard",
          cats_in_combo == {"laptop", "mouse", "keyboard"}, str(cats_in_combo))

    total = tc["expected_output"]["total_cost"]
    r.add("total_cost <= budget", total <= budget, f"{fmt_vnd(total)} <= {fmt_vnd(budget)}")

    price_errors = []
    for p in combo:
        if p["id"] not in prod_map: continue
        actual = price_after_discount(prod_map[p["id"]])
        if abs(p["price_after_discount"] - actual) >= 10:
            price_errors.append(f"{p['id']}: {fmt_vnd(p['price_after_discount'])} vs {fmt_vnd(actual)}")
    r.add("Giá sau giảm đúng", len(price_errors) == 0,
          "; ".join(price_errors) if price_errors else "OK")

    oos = [p["id"] for p in combo if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Tất cả sản phẩm còn hàng", len(oos) == 0,
          f"Hết hàng: {oos}" if oos else "OK")

    calc_score = sum(prod_map[p["id"]]["performance_score"] for p in combo if p["id"] in prod_map)
    stated_score = tc["expected_output"]["total_performance_score"]
    r.add("total_performance_score đúng", calc_score == stated_score,
          f"calc={calc_score}, stated={stated_score}")

    stated_remaining = tc["expected_output"]["remaining_budget"]
    r.add("remaining_budget = budget - total_cost",
          abs(stated_remaining - (budget - total)) < 50,
          f"calc={fmt_vnd(budget - total)}, stated={fmt_vnd(stated_remaining)}")

    best = find_best_combo(products, budget, ["laptop", "mouse", "keyboard"])
    if best:
        _, _, best_score = best
        r.add("Combo đề xuất có score tốt hoặc gần tốt nhất",
              stated_score >= best_score - 5,
              f"stated={stated_score}, optimal={best_score}")
    return r


def validate_TC004(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    prod_map = build_product_map(products)
    target_id = tc["target_product"]

    target = prod_map.get(target_id)
    r.add(f"{target_id} có stock = 0 trong mock data",
          target is not None and target["stock"] == 0,
          f"stock = {target['stock'] if target else 'NOT FOUND'}")

    r.add("expected_output.feasible = False",
          tc["expected_output"]["feasible"] is False)

    oos_list = tc["expected_output"].get("out_of_stock_items", [])
    r.add("out_of_stock_items chứa L0006",
          any("L0006" in item for item in oos_list), str(oos_list))

    fallback = tc["expected_output"].get("fallback_recommendation", {}).get("combo", [])
    r.add("Có fallback combo không rỗng", len(fallback) > 0, f"{len(fallback)} items")

    fallback_oos = [p["id"] for p in fallback if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Sản phẩm fallback còn hàng", len(fallback_oos) == 0,
          f"Hết hàng: {fallback_oos}" if fallback_oos else "OK")

    fallback_laptops = [p["id"] for p in fallback if p["id"] in prod_map and prod_map[p["id"]]["category"] == "laptop"]
    r.add("Fallback laptop khác với L0006",
          all(lid != "L0006" for lid in fallback_laptops), str(fallback_laptops))
    return r


def validate_TC005(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    prod_map = build_product_map(products)

    laptops = get_in_stock(products, "laptop")
    cheapest = min(price_after_discount(p) for p in laptops)
    r.add("Laptop rẻ nhất > 1 triệu",
          cheapest > budget, f"Laptop rẻ nhất: {fmt_vnd(cheapest)}")

    r.add("feasible = False",
          tc["expected_output"]["feasible"] is False)

    r.add("Có reason giải thích",
          bool(tc["expected_output"].get("reason")),
          tc["expected_output"].get("reason", "")[:80])

    partial = tc["expected_output"].get("partial_plan", {})
    r.add("Có partial_plan", bool(partial))

    missing = partial.get("missing", [])
    r.add("partial_plan.missing chứa 'laptop'", "laptop" in missing, str(missing))

    affordable = partial.get("affordable_combo", [])
    if affordable:
        total = sum(p["price_after_discount"] for p in affordable)
        r.add("affordable_combo tổng tiền <= budget", total <= budget, fmt_vnd(total))

        has_laptop = any(p["id"] in prod_map and prod_map[p["id"]]["category"] == "laptop" for p in affordable)
        r.add("affordable_combo không chứa laptop", not has_laptop)

        if partial.get("total"):
            r.add("partial_plan.total = sum(affordable_combo)",
                  abs(total - partial["total"]) < 50,
                  f"calc={fmt_vnd(total)}, stated={fmt_vnd(partial['total'])}")
    return r


def validate_TC006(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    combo = tc["expected_output"]["recommended_combo"]
    prod_map = build_product_map(products)

    r.add("feasible = True", tc["expected_output"]["feasible"] is True)

    oos = [p["id"] for p in combo if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Tất cả sản phẩm còn hàng", len(oos) == 0,
          f"Hết hàng: {oos}" if oos else "OK")

    price_errors = []
    for p in combo:
        if p["id"] not in prod_map: continue
        actual = price_after_discount(prod_map[p["id"]])
        if abs(p["price_after_discount"] - actual) >= 10:
            price_errors.append(f"{p['id']}: {fmt_vnd(p['price_after_discount'])} vs {fmt_vnd(actual)}")
    r.add("Giá sau giảm đúng", len(price_errors) == 0,
          "; ".join(price_errors) if price_errors else "OK")

    total = tc["expected_output"]["total_cost"]
    r.add("total_cost <= budget", total <= budget, f"{fmt_vnd(total)}")

    laptops_in_stock = sorted(get_in_stock(products, "laptop"), key=lambda x: x["discount_percent"], reverse=True)
    max_disc = laptops_in_stock[0]["discount_percent"] if laptops_in_stock else 0
    combo_laptop = next((p for p in combo if p["id"] in prod_map and prod_map[p["id"]]["category"] == "laptop"), None)
    if combo_laptop:
        stated_disc = combo_laptop["discount_percent"]
        r.add("Laptop đề xuất có discount cao (cho phép lệch 2% vì feasibility)",
              stated_disc >= max_disc - 2, f"stated={stated_disc}%, max={max_disc}%")

    r.add("Có note giải thích trade-off discount",
          bool(tc["expected_output"].get("note")),
          tc["expected_output"].get("note", "")[:80])

    stated_remaining = tc["expected_output"]["remaining_budget"]
    r.add("remaining_budget = budget - total_cost",
          abs(stated_remaining - (budget - total)) < 50,
          f"calc={fmt_vnd(budget - total)}, stated={fmt_vnd(stated_remaining)}")
    return r


def validate_TC007(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    combo = tc["expected_output"]["recommended_combo"]
    prod_map = build_product_map(products)

    r.add("feasible = True", tc["expected_output"]["feasible"] is True)

    oos = [p["id"] for p in combo if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Tất cả sản phẩm còn hàng", len(oos) == 0,
          f"Hết hàng: {oos}" if oos else "OK")

    total = tc["expected_output"]["total_cost"]
    r.add("total_cost <= budget", total <= budget)

    laptops = sorted(get_in_stock(products, "laptop"), key=lambda x: x["performance_score"], reverse=True)
    combo_laptop = next((p for p in combo if p["id"] in prod_map and prod_map[p["id"]]["category"] == "laptop"), None)
    if laptops and combo_laptop:
        sel_score = prod_map[combo_laptop["id"]]["performance_score"]
        max_score = laptops[0]["performance_score"]
        r.add("Laptop chọn có performance_score cao nhất khả thi (sai số ≤5)",
              sel_score >= max_score - 5, f"selected={sel_score}, max={max_score}")

    r.add("Có upsell_suggestion",
          bool(tc["expected_output"].get("upsell_suggestion")),
          tc["expected_output"].get("upsell_suggestion", "")[:80])

    stated_remaining = tc["expected_output"]["remaining_budget"]
    r.add("remaining_budget > 0", stated_remaining > 0, fmt_vnd(stated_remaining))
    r.add("remaining_budget = budget - total_cost",
          abs(stated_remaining - (budget - total)) < 50,
          f"calc={fmt_vnd(budget - total)}, stated={fmt_vnd(stated_remaining)}")

    calc_score = sum(prod_map[p["id"]]["performance_score"] for p in combo if p["id"] in prod_map)
    stated_score = tc["expected_output"]["total_performance_score"]
    r.add("total_performance_score đúng", calc_score == stated_score,
          f"calc={calc_score}, stated={stated_score}")
    return r


def validate_TC008(tc, products, verbose):
    r = ValidationResult(tc["test_id"])
    budget = tc["budget"]
    combo = tc["expected_output"]["recommended_combo"]
    prod_map = build_product_map(products)

    r.add("feasible = True", tc["expected_output"]["feasible"] is True)

    combo_laptop = next((p for p in combo if p["id"] in prod_map and prod_map[p["id"]]["category"] == "laptop"), None)
    if combo_laptop:
        name = prod_map[combo_laptop["id"]]["name"]
        r.add("Laptop đề xuất là HP", "HP" in name, f"name='{name}'")

    combo_mouse = next((p for p in combo if p["id"] in prod_map and prod_map[p["id"]]["category"] == "mouse"), None)
    if combo_mouse:
        name = prod_map[combo_mouse["id"]]["name"]
        r.add("Mouse đề xuất là Logitech", "Logitech" in name, f"name='{name}'")

    combo_kb = next((p for p in combo if p["id"] in prod_map and prod_map[p["id"]]["category"] == "keyboard"), None)
    if combo_kb:
        name = prod_map[combo_kb["id"]]["name"]
        r.add("Keyboard đề xuất là Logitech", "Logitech" in name, f"name='{name}'")

    oos = [p["id"] for p in combo if p["id"] in prod_map and prod_map[p["id"]]["stock"] == 0]
    r.add("Tất cả sản phẩm còn hàng", len(oos) == 0,
          f"Hết hàng: {oos}" if oos else "OK")

    price_errors = []
    for p in combo:
        if p["id"] not in prod_map: continue
        actual = price_after_discount(prod_map[p["id"]])
        if abs(p["price_after_discount"] - actual) >= 10:
            price_errors.append(f"{p['id']}: {fmt_vnd(p['price_after_discount'])} vs {fmt_vnd(actual)}")
    r.add("Giá sau giảm đúng", len(price_errors) == 0,
          "; ".join(price_errors) if price_errors else "OK")

    total = tc["expected_output"]["total_cost"]
    r.add("total_cost <= budget", total <= budget, fmt_vnd(total))

    logitech_kbs = [p for p in get_in_stock(products, "keyboard") if "Logitech" in p["name"]]
    r.add(f"Có note (chỉ có {len(logitech_kbs)} Logitech keyboard còn hàng)",
          bool(tc["expected_output"].get("note")),
          tc["expected_output"].get("note", "")[:80])

    filter_applied = tc["expected_output"].get("brand_filter_applied", {})
    r.add("brand_filter_applied có trong expected_output", bool(filter_applied), str(filter_applied))

    stated_remaining = tc["expected_output"]["remaining_budget"]
    r.add("remaining_budget = budget - total_cost",
          abs(stated_remaining - (budget - total)) < 50,
          f"calc={fmt_vnd(budget - total)}, stated={fmt_vnd(stated_remaining)}")
    return r


# ══════════════════════════════════════════════════════════
#  Report Rendering
# ══════════════════════════════════════════════════════════

VALIDATORS = {
    "TC001": validate_TC001,
    "TC002": validate_TC002,
    "TC003": validate_TC003,
    "TC004": validate_TC004,
    "TC005": validate_TC005,
    "TC006": validate_TC006,
    "TC007": validate_TC007,
    "TC008": validate_TC008,
}

def render_result(result, tc, verbose):
    status = f"{GREEN}✓ ALL PASS{RESET}" if result.passed else f"{RED}✗ {result.n_total - result.n_pass} FAILED{RESET}"
    print(f"  {BOLD}[{result.tc_id}]{RESET}  {tc.get('title','')}")
    print(f"  {DIM}Budget: {fmt_vnd(tc['budget'])}  |  Categories: {tc.get('required_categories','all')}{RESET}")
    print(f"  Status: {status}  ({result.n_pass}/{result.n_total} checks)\n")

    if verbose or not result.passed:
        for label, passed, detail in result.checks:
            icon = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
            print(f"    {icon}  {label}")
            if detail and (verbose or not passed):
                print(f"       {DIM}↳ {detail}{RESET}")
        print()

def print_summary(results):
    total_tcs    = len(results)
    passed_tcs   = sum(1 for r in results if r.passed)
    total_checks = sum(r.n_total for r in results)
    passed_checks = sum(r.n_pass for r in results)

    bar_len = 40
    filled = int(bar_len * passed_checks / total_checks) if total_checks else 0
    bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (bar_len - filled)}{RESET}"

    print(f"\n{BOLD}{'─'*62}{RESET}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{'─'*62}")
    print(f"  Test Cases : {passed_tcs}/{total_tcs} passed")
    print(f"  Checks     : {passed_checks}/{total_checks} passed")
    print(f"  Progress   : {bar} {passed_checks/total_checks*100:.0f}%")

    if passed_tcs == total_tcs:
        print(f"\n  {GREEN}{BOLD}🎉 Tất cả test case hợp lệ!{RESET}")
    else:
        failed = [r.tc_id for r in results if not r.passed]
        print(f"\n  {RED}Test case cần xem lại: {', '.join(failed)}{RESET}")

        print(f"\n  {BOLD}Chi tiết lỗi:{RESET}")
        for r in results:
            if not r.passed:
                for label, passed, detail in r.checks:
                    if not passed:
                        print(f"  {RED}✗{RESET} [{r.tc_id}] {label}")
                        if detail:
                            print(f"       {DIM}↳ {detail}{RESET}")
    print(f"{'─'*62}\n")


def main():
    parser = argparse.ArgumentParser(description="Validate Budget Agent Test Cases")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="In chi tiết tất cả checks kể cả khi pass")
    parser.add_argument("--tc", type=str, default=None,
                        help="Chỉ chạy 1 test case, ví dụ: --tc TC003")
    args = parser.parse_args()

    try:
        products   = load_json(MOCK_DATA_FILE)
        test_cases = load_json(TEST_CASE_FILE)
    except FileNotFoundError as e:
        print(f"{RED}ERROR: Không tìm thấy file: {e}{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}{'='*62}{RESET}")
    print(f"{BOLD}{CYAN}   Budget Planning Agent – Test Case Validator{RESET}")
    print(f"{BOLD}{'='*62}{RESET}\n")
    print(f"  {DIM}Mock data  : {len(products)} sản phẩm  ({MOCK_DATA_FILE}){RESET}")
    print(f"  {DIM}Test cases : {len(test_cases)} cases  ({TEST_CASE_FILE}){RESET}")
    print(f"  {DIM}Mode       : {'verbose' if args.verbose else 'normal (--verbose để xem tất cả checks)'}{RESET}\n")
    print(f"{'─'*62}\n")

    results = []
    for tc in test_cases:
        tc_id = tc["test_id"]
        if args.tc and tc_id != args.tc:
            continue
        validator = VALIDATORS.get(tc_id)
        if not validator:
            print(f"  {YELLOW}⚠ WARN{RESET}  {tc_id}: không có validator, bỏ qua.\n")
            continue
        result = validator(tc, products, args.verbose)
        results.append(result)
        render_result(result, tc, args.verbose)

    if results:
        print_summary(results)
    else:
        print(f"  {YELLOW}⚠{RESET} Không có test case nào được chạy.")


if __name__ == "__main__":
    main()