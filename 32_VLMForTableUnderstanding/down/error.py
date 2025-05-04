from lxml import html
from zss import simple_distance, Node
import os

# Define the path to the directory containing subfolders
base_dir = "/home/teaching/acc/pubtabnet/htmlPairsTest"

def parse_html(file_path):
    """Parse HTML file and return the root node"""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = html.parse(f)
    return tree.getroot()

def html_to_tree(node):
    """Convert lxml node to zss-compatible tree"""
    zss_node = Node(node.tag)
    for child in node:
        if isinstance(child.tag, str):  # Skip text/comments
            zss_node.addkid(html_to_tree(child))
    return zss_node

def get_tree_size(node):
    """Recursively count number of nodes in a zss tree"""
    return 1 + sum(get_tree_size(child) for child in node.children)

def compute_normalized_distance(tree1, tree2):
    """Compute raw and normalized tree edit distance"""
    raw_distance = simple_distance(tree1, tree2)
    size1 = get_tree_size(tree1)
    size2 = get_tree_size(tree2)
    max_size = max(size1, size2)
    if max_size == 0:
        normalized_error = 0.0
    else:
        normalized_error = raw_distance / max_size
    return raw_distance, normalized_error * 100  # return percentage

# Accumulators
total_error = 0.0
file_count = 0
failures = []

# Traverse each subdirectory
for subfolder in os.listdir(base_dir):
    subdir_path = os.path.join(base_dir, subfolder)
    if not os.path.isdir(subdir_path):
        continue

    gen_path = os.path.join(subdir_path, "generated.html")
    true_path = os.path.join(subdir_path, "true.html")

    if not os.path.exists(gen_path) or not os.path.exists(true_path):
        print(f"⚠️ Missing files in {subfolder}")
        continue

#    try:
    tree1 = html_to_tree(parse_html(gen_path))
    tree2 = html_to_tree(parse_html(true_path))
    raw_distance, error_percent = compute_normalized_distance(tree1, tree2)
    total_error += error_percent
    file_count += 1

    print(f"{subfolder}: Error = {error_percent:.2f}%")
'''    except Exception as e:
        print(f"❌ Failed to process {subfolder}: {e}")
        failures.append(subfolder)'''

# Final average
if file_count > 0:
    avg_error = total_error / file_count
    print(f"\n✅ Processed {file_count} file pairs")
    print(f"📊 Average Normalized Tree Edit Distance: {avg_error:.2f}%")
else:
    print("❌ No valid file pairs processed.")

if failures:
    print(f"\n❗ Skipped {len(failures)} due to errors: {failures}")

