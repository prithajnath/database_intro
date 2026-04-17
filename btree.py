"""
A minimal B+ tree implementation for the database tutorial demo.

This is intentionally simple and pedagogical, not production-grade:
    - Insert and search only (no deletion, no rebalancing on delete)
    - Duplicate keys allowed (multiple employees can have same salary)
    - Leaf nodes are linked left-to-right for fast range scans
    - Includes print_tree() so you can SHOW the structure to your audience

The whole point of this module is to make the audience see that:
    1. A B+ tree is a real, comprehensible data structure
    2. Point lookups walk O(log n) nodes instead of scanning O(n) rows
    3. Range queries find the start, then walk the linked leaf chain
    4. This is exactly what CREATE INDEX builds for you under the hood
"""

import bisect


class Node:
    """Base class for B+ tree nodes."""

    def __init__(self, order):
        self.order = order
        self.keys = []
        self.parent = None

    def is_full(self):
        return len(self.keys) >= self.order


class LeafNode(Node):
    """
    Leaf node: holds (key, value) pairs and a pointer to the next leaf.
    The 'next' pointer is what makes range scans fast - once we find the
    start of a range, we just walk the linked list of leaves.
    """

    def __init__(self, order):
        super().__init__(order)
        self.values = []  # parallel to self.keys; each entry is a list (for duplicates)
        self.next = None  # linked-list pointer to next leaf
        self.is_leaf = True

    def insert(self, key, value):
        """Insert a key/value into this leaf, keeping keys sorted."""
        idx = bisect.bisect_left(self.keys, key)
        if idx < len(self.keys) and self.keys[idx] == key:
            # Duplicate key - append value to existing bucket
            self.values[idx].append(value)
        else:
            self.keys.insert(idx, key)
            self.values.insert(idx, [value])

    def split(self):
        """
        Split a full leaf into two. Returns (new_leaf, promoted_key).
        The promoted key is the first key of the new (right) leaf -
        in a B+ tree, the separator key also still lives in the leaves.
        """
        mid = len(self.keys) // 2
        new_leaf = LeafNode(self.order)
        new_leaf.keys = self.keys[mid:]
        new_leaf.values = self.values[mid:]
        self.keys = self.keys[:mid]
        self.values = self.values[:mid]

        # Maintain the linked list of leaves
        new_leaf.next = self.next
        self.next = new_leaf

        return new_leaf, new_leaf.keys[0]


class InternalNode(Node):
    """
    Internal node: holds separator keys and pointers to child nodes.
    Always has len(children) == len(keys) + 1.
    """

    def __init__(self, order):
        super().__init__(order)
        self.children = []
        self.is_leaf = False

    def split(self):
        """
        Split a full internal node. Unlike leaves, the middle key is
        promoted UP and removed from both halves.
        """
        mid = len(self.keys) // 2
        promoted_key = self.keys[mid]

        new_node = InternalNode(self.order)
        new_node.keys = self.keys[mid + 1 :]
        new_node.children = self.children[mid + 1 :]
        for child in new_node.children:
            child.parent = new_node

        self.keys = self.keys[:mid]
        self.children = self.children[: mid + 1]

        return new_node, promoted_key


class BPlusTree:
    """
    A B+ tree supporting insert, point search, and range search.

    The 'order' parameter controls the fan-out: a node can hold up to
    `order` keys before it needs to split. Higher order = shallower tree
    = fewer disk reads in a real database. We use 32 by default which
    keeps the tree shallow even for millions of keys.
    """

    def __init__(self, order=32):
        if order < 3:
            raise ValueError("order must be >= 3")
        self.order = order
        self.root = LeafNode(order)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _find_leaf(self, key):
        """Walk from root to the leaf where `key` should live."""
        node = self.root
        while not node.is_leaf:
            # Find the first separator key strictly greater than `key`;
            # the child to its left is the one we descend into.
            idx = bisect.bisect_right(node.keys, key)
            node = node.children[idx]
        return node

    def search(self, key):
        """
        Point lookup: return the list of values associated with `key`,
        or an empty list if the key doesn't exist.
        """
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return list(leaf.values[idx])
        return []

    def range_search(self, low, high):
        """
        Range query: return all values whose keys fall in [low, high].

        This is where B+ trees shine: we descend ONCE to find the leaf
        containing `low`, then walk the linked list of leaves rightward
        until we pass `high`. No more tree traversals needed.
        """
        results = []
        leaf = self._find_leaf(low)

        while leaf is not None:
            for k, v_list in zip(leaf.keys, leaf.values):
                if k < low:
                    continue
                if k > high:
                    return results
                results.extend(v_list)
            leaf = leaf.next  # follow the leaf chain

        return results

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert(self, key, value):
        """Insert (key, value) into the tree, splitting nodes as needed."""
        leaf = self._find_leaf(key)
        leaf.insert(key, value)

        if leaf.is_full():
            self._split_and_propagate(leaf)

    def _split_and_propagate(self, node):
        """Split a full node and push the promoted key up to the parent."""
        new_node, promoted_key = node.split()

        if node is self.root:
            # Tree grows in height by one
            new_root = InternalNode(self.order)
            new_root.keys = [promoted_key]
            new_root.children = [node, new_node]
            node.parent = new_root
            new_node.parent = new_root
            self.root = new_root
            return

        parent = node.parent
        # Insert promoted_key + new_node into the parent in sorted order
        idx = bisect.bisect_right(parent.keys, promoted_key)
        parent.keys.insert(idx, promoted_key)
        parent.children.insert(idx + 1, new_node)
        new_node.parent = parent

        if parent.is_full():
            self._split_and_propagate(parent)

    # ------------------------------------------------------------------
    # Inspection helpers (for the live demo)
    # ------------------------------------------------------------------

    def height(self):
        """Return the height of the tree (number of levels)."""
        h = 1
        node = self.root
        while not node.is_leaf:
            h += 1
            node = node.children[0]
        return h

    def leaf_count(self):
        """Count leaves by walking the linked list."""
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        count = 0
        while node is not None:
            count += 1
            node = node.next
        return count

    def print_tree(self, max_keys_per_node=6):
        """
        Print a compact ASCII view of the tree, level by level.
        Truncates each node's key list so the output stays readable.
        """

        def fmt(keys):
            if len(keys) <= max_keys_per_node:
                return str(keys)
            head = keys[: max_keys_per_node // 2]
            tail = keys[-max_keys_per_node // 2 :]
            return f"[{', '.join(map(str, head))}, ..., {', '.join(map(str, tail))}]"

        print(
            f"B+ Tree (order={self.order}, height={self.height()}, "
            f"leaves={self.leaf_count()})"
        )

        level = [self.root]
        depth = 0
        while level:
            label = "root" if depth == 0 else f"L{depth}"
            print(f"  {label}:")
            next_level = []
            # Only show first few nodes per level so output stays readable
            shown = level[:4]
            for node in shown:
                kind = "leaf" if node.is_leaf else "internal"
                print(f"    {kind} {fmt(node.keys)}")
                if not node.is_leaf:
                    next_level.extend(node.children)
            if len(level) > len(shown):
                print(f"    ... and {len(level) - len(shown)} more nodes")
            if not level[0].is_leaf:
                # Gather ALL children for the next level (not just shown)
                next_level = []
                for node in level:
                    next_level.extend(node.children)
            level = next_level
            depth += 1
            if level and level[0].is_leaf and depth > 0:
                # Print the leaf level once and stop
                label = f"L{depth}"
                print(f"  {label} (leaves, linked):")
                shown = level[:4]
                for node in shown:
                    print(f"    leaf {fmt(node.keys)} -> next")
                if len(level) > len(shown):
                    print(f"    ... and {len(level) - len(shown)} more leaves")
                break


# ----------------------------------------------------------------------
# Quick self-test: run `python btree.py` to see the tree in action
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import random

    random.seed(0)
    tree = BPlusTree(order=5)  # small order so the tree splits visibly

    # Insert 50 random salaries, each mapped to a fake employee_id
    for emp_id in range(1, 51):
        salary = random.randint(50_000, 150_000)
        tree.insert(salary, emp_id)

    print("--- Tree structure ---")
    tree.print_tree()

    print("\n--- Point lookup ---")
    # Pick a key we know exists by walking to the first leaf
    node = tree.root
    while not node.is_leaf:
        node = node.children[0]
    sample_key = node.keys[0]
    print(f"search({sample_key}) -> {tree.search(sample_key)}")

    print("\n--- Range query ---")
    results = tree.range_search(80_000, 90_000)
    print(f"range_search(80000, 90000) -> {len(results)} employees")
