from typing import List, Dict, Tuple
import gradio as gr


# scoring and input checking

def compute_score(item: Dict) -> float:
    # bigger score means the item should be handled earlier
    return item["user_priority"] * 100 + item["fragility"] * 20 - item["weight"]


def parse_items(raw_text: str) -> List[Dict]:
    # input format: label, weight, fragility, priority
    if not raw_text or not raw_text.strip():
        raise ValueError(
            "Please enter at least one item in the format: label, weight, fragility, priority"
        )

    items: List[Dict] = []
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]

    for idx, line in enumerate(lines, start=1):
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            raise ValueError(
                f"Line {idx} is invalid. Each line needs 4 values: "
                "label, weight, fragility, priority"
            )

        label, weight_str, fragility_str, priority_str = parts

        if not label:
            raise ValueError(f"Line {idx} has an empty label.")

        try:
            weight = float(weight_str)
        except ValueError:
            raise ValueError(f"Line {idx}: weight must be a number.")

        try:
            fragility = int(fragility_str)
            priority = int(priority_str)
        except ValueError:
            raise ValueError(f"Line {idx}: fragility and priority must be whole numbers.")

        if weight < 0:
            raise ValueError(f"Line {idx}: weight cannot be negative.")
        if not 1 <= fragility <= 5:
            raise ValueError(f"Line {idx}: fragility must be between 1 and 5.")
        if not 1 <= priority <= 5:
            raise ValueError(f"Line {idx}: priority must be between 1 and 5.")

        item = {
            "label": label,
            "weight": weight,
            "fragility": fragility,
            "user_priority": priority,
        }
        item["score"] = compute_score(item)
        items.append(item)

    return items


# merge sort steps

def short_item(item: Dict) -> str:
    return (
        f"{item['label']} "
        f"(score={item['score']:.1f}, priority={item['user_priority']}, "
        f"fragility={item['fragility']}, weight={item['weight']})"
    )


def list_to_block(items: List[Dict]) -> str:
    if not items:
        return "[]"
    return "\n".join(f"- {short_item(item)}" for item in items)


def merge_with_steps(left: List[Dict], right: List[Dict], steps: List[str], depth: int) -> List[Dict]:
    indent = "  " * depth
    merged: List[Dict] = []
    i = 0
    j = 0

    steps.append(
        f"{indent}Merging these lists:\n"
        f"{indent}Left side:\n{indent}{list_to_block(left).replace(chr(10), chr(10) + indent)}\n"
        f"{indent}Right side:\n{indent}{list_to_block(right).replace(chr(10), chr(10) + indent)}"
    )

    while i < len(left) and j < len(right):
        left_item = left[i]
        right_item = right[j]

        steps.append(
            f"{indent}Comparing:\n"
            f"{indent}- {short_item(left_item)}\n"
            f"{indent}- {short_item(right_item)}"
        )

        # sort from highest score to lowest
        if left_item["score"] >= right_item["score"]:
            merged.append(left_item)
            steps.append(f"{indent}Taking left item: {left_item['label']}")
            i += 1
        else:
            merged.append(right_item)
            steps.append(f"{indent}Taking right item: {right_item['label']}")
            j += 1

    while i < len(left):
        merged.append(left[i])
        steps.append(f"{indent}Left side has one item left: {left[i]['label']}")
        i += 1

    while j < len(right):
        merged.append(right[j])
        steps.append(f"{indent}Right side has one item left: {right[j]['label']}")
        j += 1

    steps.append(
        f"{indent}Merged list:\n"
        f"{indent}{list_to_block(merged).replace(chr(10), chr(10) + indent)}"
    )
    return merged


def merge_sort_with_steps(items: List[Dict], steps: List[str], depth: int = 0) -> List[Dict]:
    indent = "  " * depth

    if len(items) <= 1:
        steps.append(
            f"{indent}Reached base case:\n"
            f"{indent}{list_to_block(items).replace(chr(10), chr(10) + indent)}"
        )
        return items[:]

    mid = len(items) // 2
    left = items[:mid]
    right = items[mid:]

    steps.append(
        f"{indent}Splitting the list:\n"
        f"{indent}Left side:\n{indent}{list_to_block(left).replace(chr(10), chr(10) + indent)}\n"
        f"{indent}Right side:\n{indent}{list_to_block(right).replace(chr(10), chr(10) + indent)}"
    )

    sorted_left = merge_sort_with_steps(left, steps, depth + 1)
    sorted_right = merge_sort_with_steps(right, steps, depth + 1)
    return merge_with_steps(sorted_left, sorted_right, steps, depth)


# output text

def format_ranked_table(items: List[Dict]) -> str:
    lines = [
        "| Rank | Label | Weight | Fragility | User Priority | Score |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"| {idx} | {item['label']} | {item['weight']} | {item['fragility']} | "
            f"{item['user_priority']} | {item['score']:.1f} |"
        )
    return "\n".join(lines)


def explain_score_rule() -> str:
    return (
        "### Score Rule\n"
        "- **Higher user priority** matters most.\n"
        "- **More fragile** items should be handled earlier.\n"
        "- **Lighter** items are a little easier to place or unpack first.\n\n"
        "**Score = user priority × 100 + fragility × 20 − weight**\n\n"
        "The app uses **Merge Sort** to sort items by this score in descending order."
    )


def run_simulation(raw_text: str) -> Tuple[str, str, str]:
    try:
        items = parse_items(raw_text)
    except ValueError as exc:
        return (
            f"### Input Error\n{exc}",
            "",
            explain_score_rule(),
        )

    steps: List[str] = []
    sorted_items = merge_sort_with_steps(items, steps)

    result_md = (
        "## Final Packing Order\n"
        "Items with a **higher score** should be packed or unpacked earlier.\n\n"
        + format_ranked_table(sorted_items)
    )

    steps_md = "## Merge Sort Steps\n\n" + "\n\n---\n\n".join(
        f"**Step {idx}:**\n\n{step}" for idx, step in enumerate(steps, start=1)
    )

    return result_md, steps_md, explain_score_rule()


SAMPLE_INPUT = """Laptop Box, 4, 5, 5
Kitchen Plates, 12, 5, 4
Desk Lamp, 6, 3, 3
Winter Clothes Bin, 10, 1, 2
Toiletries Bag, 2, 2, 5
Textbooks, 15, 1, 3"""


with gr.Blocks(title="Move-In Packing Priority Simulator") as demo:
    gr.Markdown(
        """
# Move-In Packing Priority Simulator
This app sorts move-in items using **Merge Sort**.

Enter one item per line in this format:

`label, weight, fragility, priority`

- **weight**: any non-negative number
- **fragility**: integer from 1 to 5
- **priority**: integer from 1 to 5
"""
    )

    with gr.Row():
        input_box = gr.Textbox(
            label="Packing Items",
            lines=10,
            value=SAMPLE_INPUT,
            placeholder="Laptop Box, 4, 5, 5",
        )

    with gr.Row():
        sort_button = gr.Button("Run Merge Sort")

    rule_output = gr.Markdown()
    result_output = gr.Markdown()
    steps_output = gr.Markdown()

    sort_button.click(
        fn=run_simulation,
        inputs=input_box,
        outputs=[result_output, steps_output, rule_output],
    )

    gr.Markdown(
        """
### What the app shows
- the final packing order
- the merge sort steps
- the score rule used for sorting
"""
    )

if __name__ == "__main__":
    demo.launch()
