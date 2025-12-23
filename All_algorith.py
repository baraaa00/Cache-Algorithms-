import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


# ---------------- Cache Algorithms (Fixed) ---------------- #
def fifo(requests, cache_size):
    cache, q, steps = [], [], []
    for r in requests:
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                q.append(r)
                action = "MISS - Added"
            else:
                replaced = q.pop(0)
                idx = cache.index(replaced)
                cache[idx] = r
                q.append(r)
                action = f"MISS - Replace {replaced}"
        else:
            action = "HIT"
        steps.append((r, action, list(cache), replaced))
    return steps


def lifo(requests, cache_size):
    cache, stack, steps = [], [], []
    for r in requests:
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                stack.append(r)
                action = "MISS - Added"
            else:
                replaced = stack.pop(-1)
                idx = cache.index(replaced)
                cache[idx] = r
                stack.append(r)
                action = f"MISS - Replace {replaced}"
        else:
            action = "HIT"
        steps.append((r, action, list(cache), replaced))
    return steps


def optimal(requests, cache_size):
    cache, steps = [], []
    for i, r in enumerate(requests):
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                action = "MISS - Added"
            else:
                future = requests[i + 1:]
                farthest, idx = -1, 0
                for c in cache:
                    pos = future.index(c) if c in future else float("inf")
                    if pos > farthest:
                        farthest, idx = pos, cache.index(c)
                replaced = cache[idx]
                cache[idx] = r
                action = f"MISS - Replace {replaced}"
        else:
            action = "HIT"
        steps.append((r, action, list(cache), replaced))
    return steps


def lru(requests, cache_size):
    cache, recent, steps = [], [], []
    for r in requests:
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                action = "MISS - Added"
            else:
                replaced = recent.pop(0)
                idx = cache.index(replaced)
                cache[idx] = r
                action = f"MISS - Replace {replaced}"
        else:
            action = "HIT"
        if r in recent:
            recent.remove(r)
        recent.append(r)
        steps.append((r, action, list(cache), replaced))
    return steps


def mru(requests, cache_size):
    cache, recent, steps = [], [], []
    for r in requests:
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                action = "MISS - Added"
            else:
                replaced = recent.pop(-1)
                idx = cache.index(replaced)
                cache[idx] = r
                action = f"MISS - Replace {replaced}"
        else:
            action = "HIT"
        if r in recent:
            recent.remove(r)
        recent.append(r)
        steps.append((r, action, list(cache), replaced))
    return steps


# --- تم التعديل هنا: Tree-based Pseudo-LRU ---
def pseudo_lru(requests, cache_size):
    """
    Tree-based Pseudo-LRU Algorithm.
    Uses a binary tree of bits to point to the pseudo-LRU victim.
    When a block is accessed, bits on the path to it are flipped to point away.
    """
    cache = []
    steps = []
    # Tree bits to store directions (0=Left, 1=Right)
    # Size 4*cache_size ensures we have enough nodes for the tree heap
    tree_bits = [0] * (cache_size * 4)

    def update_tree(target_idx):
        # Update path to point AWAY from the accessed item (Make it MRU)
        node = 0
        left, right = 0, cache_size
        while right - left > 1:
            mid = (left + right) // 2
            if target_idx < mid:
                # Target is Left, point arrow Right (1) to protect Left
                tree_bits[node] = 1
                node = 2 * node + 1
                right = mid
            else:
                # Target is Right, point arrow Left (0) to protect Right
                tree_bits[node] = 0
                node = 2 * node + 2
                left = mid

    def find_victim():
        # Follow arrows to find the victim (PLRU item)
        node = 0
        left, right = 0, cache_size
        while right - left > 1:
            mid = (left + right) // 2
            if tree_bits[node] == 0:
                # Arrow points Left, go Left
                node = 2 * node + 1
                right = mid
            else:
                # Arrow points Right, go Right
                node = 2 * node + 2
                left = mid
        return left

    for r in requests:
        action, replaced = "", None

        if r in cache:
            # HIT
            action = "HIT"
            idx = cache.index(r)
            update_tree(idx)  # Protect this item
        else:
            if len(cache) < cache_size:
                # Cache not full
                cache.append(r)
                idx = len(cache) - 1
                action = "MISS - Added"
                update_tree(idx)  # Protect new item
            else:
                # Cache full, need replacement
                victim_idx = find_victim()
                replaced = cache[victim_idx]
                cache[victim_idx] = r
                action = f"MISS - Replace {replaced}"
                update_tree(victim_idx)  # Protect new item

        steps.append((r, action, list(cache), replaced))

    return steps


def lfu(requests, cache_size):
    cache, freq, steps = [], {}, []
    for r in requests:
        action, replaced = "", None
        if r not in cache:
            if len(cache) < cache_size:
                cache.append(r)
                action = "MISS - Added"
            else:
                least = min(freq[c] for c in cache)
                candidates = [c for c in cache if freq[c] == least]
                replaced = candidates[0]
                idx = cache.index(replaced)
                cache[idx] = r
                action = f"MISS - Replace {replaced}"
            freq[r] = freq.get(r, 0)
        else:
            action = "HIT"
        freq[r] = freq.get(r, 0) + 1
        steps.append((r, action, list(cache), replaced))
    return steps


# ---------------- Animated Visualization ---------------- #
class AnimatedCacheVisualizer(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.cache_slots = []
        self.memory_items = []

    def initialize_visualization(self, cache_size, all_requests):
        self.delete("all")
        self.cache_slots = []
        self.memory_items = []

        unique_items = list(dict.fromkeys(all_requests))

        # Main Memory Section
        self.create_text(120, 30, text="💾 MAIN MEMORY",
                         font=("Arial", 14, "bold"), fill="#4ecdc4", anchor="w")

        mem_y = 65
        for i, item in enumerate(unique_items[:12]):
            x = 120 + (i % 6) * 75
            y = mem_y + (i // 6) * 60

            rect = self.create_rectangle(x, y, x + 60, y + 45,
                                         fill="#2c3e50", outline="#4ecdc4", width=2)
            text = self.create_text(x + 30, y + 22, text=str(item),
                                    font=("Arial", 12, "bold"), fill="white")
            self.memory_items.append({'item': item, 'rect': rect, 'text': text})

        # Cache Memory Section
        cache_y = 240
        self.create_text(120, cache_y - 25, text="⚡ CACHE MEMORY",
                         font=("Arial", 14, "bold"), fill="#f39c12", anchor="w")

        for i in range(cache_size):
            x = 120 + i * 100
            y = cache_y

            slot_rect = self.create_rectangle(x, y, x + 85, y + 70,
                                              fill="#34495e", outline="#95a5a6", width=3)

            self.create_text(x + 42, y - 12, text=f"Slot {i + 1}",
                             font=("Arial", 9, "bold"), fill="#95a5a6")

            content_text = self.create_text(x + 42, y + 35, text="EMPTY",
                                            font=("Arial", 14, "bold"), fill="#7f8c8d")

            self.cache_slots.append({
                'rect': slot_rect,
                'text': content_text,
                'value': None
            })

        self.create_text(120, 380, text="📊 STATUS",
                         font=("Arial", 13, "bold"), fill="#9b59b6", anchor="w")

    def animate_request(self, request, action, cache_state, replaced, callback):
        # Highlight memory item
        for mem in self.memory_items:
            if mem['item'] == request:
                self.itemconfig(mem['rect'], fill="#3498db", outline="#4ecdc4", width=4)
                self.itemconfig(mem['text'], fill="#f1c40f")
                self.after(300, lambda m=mem: self.itemconfig(m['rect'], fill="#2c3e50", width=2))
                self.after(300, lambda m=mem: self.itemconfig(m['text'], fill="white"))
                break

        # Moving item animation
        move_item = self.create_rectangle(450, 150, 510, 200,
                                          fill="#f39c12", outline="#e74c3c", width=4)
        move_text = self.create_text(480, 175, text=str(request),
                                     font=("Arial", 16, "bold"), fill="#000")

        # Animate movement
        self.after(350, lambda: self.animate_move(move_item, move_text, 480, 175, 380, 275,
                                                  lambda: self.finish_animation(move_item, move_text, request, action,
                                                                                cache_state, replaced, callback)))

    def animate_move(self, item, text, x1, y1, x2, y2, callback):
        steps = 15
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def step(n):
            if n >= steps:
                callback()
                return
            self.move(item, dx, dy)
            self.move(text, dx, dy)
            self.after(20, lambda: step(n + 1))

        step(0)

    def finish_animation(self, item, text, request, action, cache_state, replaced, callback):
        self.delete(item)
        self.delete(text)

        # Update cache slots
        for i, slot in enumerate(self.cache_slots):
            if i < len(cache_state):
                value = cache_state[i]
                slot['value'] = value
                self.itemconfig(slot['text'], text=str(value), fill="white",
                                font=("Arial", 14, "bold"))

                if value == request:
                    # Newly added item
                    self.itemconfig(slot['rect'], fill="#27ae60", outline="#2ecc71", width=5)
                else:
                    # Other items in cache
                    self.itemconfig(slot['rect'], fill="#34495e", outline="#95a5a6", width=3)
            else:
                slot['value'] = None
                self.itemconfig(slot['text'], text="EMPTY", fill="#7f8c8d")
                self.itemconfig(slot['rect'], fill="#34495e", outline="#95a5a6", width=3)

        # Show result
        if "HIT" in action:
            color, txt_color, txt = "#27ae60", "#2ecc71", "✓ CACHE HIT!"
        else:
            color, txt_color, txt = "#c0392b", "#e74c3c", "✗ CACHE MISS!"

        result_box = self.create_rectangle(550, 230, 700, 290,
                                           fill=color, outline="white", width=4)
        result_text = self.create_text(625, 260, text=txt,
                                       font=("Arial", 15, "bold"), fill=txt_color)

        self.after(500, lambda: self.delete(result_box))
        self.after(500, lambda: self.delete(result_text))
        self.after(600, callback)


# ---------------- Analysis Section ---------------- #
class AnalysisTab:
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Create a notebook for multiple analysis tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Basic Statistics
        self.stats_frame = tk.Frame(self.notebook, bg="#2c3e50")
        self.notebook.add(self.stats_frame, text="📈 Basic Statistics")

        # Tab 2: Algorithm Comparison
        self.comparison_frame = tk.Frame(self.notebook, bg="#2c3e50")
        self.notebook.add(self.comparison_frame, text="⚖ Algorithm Comparison")

        # Tab 3: Detailed Analysis
        self.detailed_frame = tk.Frame(self.notebook, bg="#2c3e50")
        self.notebook.add(self.detailed_frame, text="🔍 Detailed Analysis")

    def update_analysis(self, algorithm_results, algorithm_name, requests, cache_size):
        """Update all analysis tabs with new data"""
        self.update_basic_stats(algorithm_results, algorithm_name, requests, cache_size)
        self.update_detailed_analysis(algorithm_results, requests, cache_size)

    def update_basic_stats(self, results, algo_name, requests, cache_size):
        """Update basic statistics tab"""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        # Calculate statistics
        total_requests = len(results)
        hits = sum(1 for r in results if r[1] == "HIT")
        misses = total_requests - hits
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = 100 - hit_rate

        # Request frequency analysis
        request_counter = Counter(requests)
        most_common = request_counter.most_common(3)
        unique_requests = len(request_counter)

        # Cache utilization
        final_cache = results[-1][2] if results else []
        cache_utilization = (len(final_cache) / cache_size * 100) if cache_size > 0 else 0

        # Create statistics display
        tk.Label(self.stats_frame, text=f"📊 {algo_name} ANALYSIS",
                 font=("Arial", 16, "bold"), bg="#2c3e50", fg="#4ecdc4").pack(pady=10)

        # Create two columns
        left_frame = tk.Frame(self.stats_frame, bg="#2c3e50")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        right_frame = tk.Frame(self.stats_frame, bg="#2c3e50")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Left column - Performance Metrics
        metrics = [
            ("Total Requests", f"{total_requests}"),
            ("Cache Hits", f"{hits} ({hit_rate:.1f}%)"),
            ("Cache Misses", f"{misses} ({miss_rate:.1f}%)"),
            ("Hit Rate", f"{hit_rate:.2f}%"),
            ("Miss Rate", f"{miss_rate:.2f}%"),
            ("Cache Size", f"{cache_size} slots"),
        ]

        tk.Label(left_frame, text="🎯 PERFORMANCE METRICS",
                 font=("Arial", 12, "bold"), bg="#2c3e50", fg="#f39c12").pack(pady=5, anchor=tk.W)

        for label, value in metrics:
            frame = tk.Frame(left_frame, bg="#34495e")
            frame.pack(fill=tk.X, pady=2, padx=5)
            tk.Label(frame, text=label, font=("Arial", 10),
                     bg="#34495e", fg="#ecf0f1").pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=value, font=("Arial", 10, "bold"),
                     bg="#34495e", fg="#2ecc71").pack(side=tk.RIGHT, padx=5)

        # Right column - Request Analysis
        tk.Label(right_frame, text="📝 REQUEST ANALYSIS",
                 font=("Arial", 12, "bold"), bg="#2c3e50", fg="#9b59b6").pack(pady=5, anchor=tk.W)

        analysis_metrics = [
            ("Unique Requests", f"{unique_requests}"),
            ("Cache Utilization", f"{cache_utilization:.1f}%"),
            ("Most Frequent", f"{most_common[0][0]} ({most_common[0][1]}x)" if most_common else "N/A"),
            ("2nd Most Frequent", f"{most_common[1][0]} ({most_common[1][1]}x)" if len(most_common) > 1 else "N/A"),
            ("3rd Most Frequent", f"{most_common[2][0]} ({most_common[2][1]}x)" if len(most_common) > 2 else "N/A"),
        ]

        for label, value in analysis_metrics:
            frame = tk.Frame(right_frame, bg="#34495e")
            frame.pack(fill=tk.X, pady=2, padx=5)
            tk.Label(frame, text=label, font=("Arial", 10),
                     bg="#34495e", fg="#ecf0f1").pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=value, font=("Arial", 10, "bold"),
                     bg="#34495e", fg="#e74c3c" if "Frequent" in label else "#3498db").pack(side=tk.RIGHT, padx=5)

        # Efficiency Rating
        efficiency = self.calculate_efficiency(hit_rate)
        tk.Label(self.stats_frame, text=f"🏆 EFFICIENCY RATING: {efficiency}",
                 font=("Arial", 12, "bold"), bg="#2c3e50",
                 fg="#27ae60" if efficiency in ["Excellent",
                                                "Good"] else "#f39c12" if efficiency == "Average" else "#e74c3c").pack(
            pady=10)

    def update_detailed_analysis(self, results, requests, cache_size):
        """Update detailed analysis tab"""
        for widget in self.detailed_frame.winfo_children():
            widget.destroy()

        # Calculate hit/miss patterns
        hit_pattern = [1 if r[1] == "HIT" else 0 for r in results]
        miss_pattern = [1 if r[1] != "HIT" else 0 for r in results]

        # Calculate running hit rate
        running_hit_rates = []
        hits_so_far = 0
        for i, r in enumerate(results, 1):
            hits_so_far += 1 if r[1] == "HIT" else 0
            running_hit_rates.append((hits_so_far / i) * 100)

        # Create detailed analysis display
        tk.Label(self.detailed_frame, text="📈 PERFORMANCE OVER TIME",
                 font=("Arial", 14, "bold"), bg="#2c3e50", fg="#4ecdc4").pack(pady=10)

        # Create figure for matplotlib
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.patch.set_facecolor('#2c3e50')

        # Plot 1: Hit/Miss Pattern
        axes[0, 0].bar(range(len(hit_pattern)), hit_pattern, color='#2ecc71', label='Hits', alpha=0.6)
        axes[0, 0].bar(range(len(miss_pattern)), miss_pattern, bottom=hit_pattern,
                       color='#e74c3c', label='Misses', alpha=0.6)
        axes[0, 0].set_title('Hit/Miss Pattern', color='white', fontsize=12)
        axes[0, 0].set_xlabel('Request Number', color='white')
        axes[0, 0].set_ylabel('Status', color='white')
        axes[0, 0].legend()
        axes[0, 0].set_facecolor('#34495e')
        axes[0, 0].tick_params(colors='white')

        # Plot 2: Running Hit Rate
        axes[0, 1].plot(running_hit_rates, color='#3498db', linewidth=2)
        axes[0, 1].fill_between(range(len(running_hit_rates)), running_hit_rates, alpha=0.3, color='#3498db')
        axes[0, 1].set_title('Running Hit Rate', color='white', fontsize=12)
        axes[0, 1].set_xlabel('Request Number', color='white')
        axes[0, 1].set_ylabel('Hit Rate (%)', color='white')
        axes[0, 1].set_facecolor('#34495e')
        axes[0, 1].tick_params(colors='white')
        axes[0, 1].grid(True, alpha=0.3)

        # Plot 3: Request Frequency
        request_counter = Counter(requests)
        items, counts = zip(*request_counter.most_common(8)) if request_counter else ([], [])
        axes[1, 0].bar(items, counts, color='#9b59b6', alpha=0.7)
        axes[1, 0].set_title('Request Frequency (Top 8)', color='white', fontsize=12)
        axes[1, 0].set_xlabel('Request Item', color='white')
        axes[1, 0].set_ylabel('Frequency', color='white')
        axes[1, 0].set_facecolor('#34495e')
        axes[1, 0].tick_params(colors='white')

        # Plot 4: Cache State Evolution
        cache_states = [len(r[2]) for r in results]
        axes[1, 1].plot(cache_states, color='#f39c12', linewidth=2)
        axes[1, 1].set_title('Cache Occupancy Over Time', color='white', fontsize=12)
        axes[1, 1].set_xlabel('Request Number', color='white')
        axes[1, 1].set_ylabel('Items in Cache', color='white')
        axes[1, 1].set_ylim(0, cache_size)
        axes[1, 1].set_facecolor('#34495e')
        axes[1, 1].tick_params(colors='white')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        # Embed matplotlib figure in tkinter
        canvas = FigureCanvasTkAgg(fig, self.detailed_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add summary statistics below the plots
        summary_frame = tk.Frame(self.detailed_frame, bg="#2c3e50")
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        summary_stats = [
            ("Longest Hit Streak", self.find_longest_streak(hit_pattern)),
            ("Longest Miss Streak", self.find_longest_streak(miss_pattern)),
            ("Average Cache Fill", f"{sum(cache_states) / len(cache_states):.1f} items"),
            ("Final Cache State", ', '.join(map(str, results[-1][2])) if results else "Empty"),
        ]

        for i, (label, value) in enumerate(summary_stats):
            frame = tk.Frame(summary_frame, bg="#34495e", relief=tk.RAISED, bd=1)
            frame.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="nsew")
            tk.Label(frame, text=label, font=("Arial", 9),
                     bg="#34495e", fg="#95a5a6").pack(pady=2)
            tk.Label(frame, text=str(value), font=("Arial", 10, "bold"),
                     bg="#34495e", fg="white").pack(pady=2)

        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)

    def update_comparison(self, all_results):
        """Update algorithm comparison tab"""
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()

        if not all_results:
            tk.Label(self.comparison_frame, text="Run multiple algorithms to compare",
                     font=("Arial", 12), bg="#2c3e50", fg="#95a5a6").pack(pady=50)
            return

        # Prepare comparison data
        algorithms = list(all_results.keys())
        hit_rates = []

        for algo, results in all_results.items():
            total = len(results)
            hits = sum(1 for r in results if r[1] == "HIT")
            hit_rate = (hits / total * 100) if total > 0 else 0
            hit_rates.append(hit_rate)

        # Create comparison chart
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#2c3e50')
        ax.set_facecolor('#34495e')

        colors = ['#2ecc71', '#3498db', '#9b59b6', '#f39c12', '#e74c3c', '#1abc9c', '#d35400']
        bars = ax.bar(algorithms, hit_rates, color=colors[:len(algorithms)], alpha=0.8)

        ax.set_title('Algorithm Comparison - Hit Rates', color='white', fontsize=14, pad=20)
        ax.set_xlabel('Algorithm', color='white', fontsize=12)
        ax.set_ylabel('Hit Rate (%)', color='white', fontsize=12)
        ax.set_ylim(0, max(hit_rates) * 1.2 if hit_rates else 100)

        # Add value labels on bars
        for bar, rate in zip(bars, hit_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', color='white', fontsize=10)

        ax.tick_params(axis='x', rotation=45, colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.grid(True, alpha=0.3, color='white')

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.comparison_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add ranking
        ranking_frame = tk.Frame(self.comparison_frame, bg="#2c3e50")
        ranking_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(ranking_frame, text="🏅 ALGORITHM RANKING",
                 font=("Arial", 12, "bold"), bg="#2c3e50", fg="#f39c12").pack(pady=5)

        # Sort algorithms by hit rate
        ranked = sorted(zip(algorithms, hit_rates), key=lambda x: x[1], reverse=True)

        for i, (algo, rate) in enumerate(ranked):
            frame = tk.Frame(ranking_frame, bg="#34495e")
            frame.pack(fill=tk.X, pady=2, padx=20)

            # Medal emojis
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i + 1}."

            tk.Label(frame, text=f"{medal} {algo}", font=("Arial", 10, "bold"),
                     bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=f"{rate:.2f}%", font=("Arial", 10, "bold"),
                     bg="#34495e", fg="#2ecc71" if i < 3 else "#3498db").pack(side=tk.RIGHT, padx=5)

    def calculate_efficiency(self, hit_rate):
        """Calculate efficiency rating based on hit rate"""
        if hit_rate >= 80:
            return "Excellent"
        elif hit_rate >= 60:
            return "Good"
        elif hit_rate >= 40:
            return "Average"
        elif hit_rate >= 20:
            return "Poor"
        else:
            return "Very Poor"

    def find_longest_streak(self, pattern):
        """Find the longest streak of 1s in a binary pattern"""
        max_streak = 0
        current_streak = 0

        for value in pattern:
            if value == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak


# ---------------- Main Application ---------------- #
class CacheSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Cache Replacement Simulator with Analysis")
        self.root.geometry("1450x900")
        self.root.configure(bg="#1a1a2e")

        self.algorithms = {
            "FIFO": fifo, "LIFO": lifo, "OPTIMAL": optimal,
            "LRU": lru, "MRU": mru, "Pseudo-LRU": pseudo_lru, "LFU": lfu
        }

        self.algo_descriptions = {
            "FIFO": "🔄 First In First Out - Replaces oldest item",
            "LIFO": "🔃 Last In First Out - Replaces newest item",
            "OPTIMAL": "🎯 Optimal - Replaces item not needed longest",
            "LRU": "⏰ Least Recently Used - Replaces least recent",
            "MRU": "⚡ Most Recently Used - Replaces most recent",
            "Pseudo-LRU": "🔀 Tree-Based PLRU - Uses tree bits",
            "LFU": "📊 Least Frequently Used - Replaces least used"
        }

        self.current_results = []
        self.current_step = 0
        self.is_running = False
        self.animation_speed = 1000
        self.all_algorithm_results = {}  # Store results for comparison

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("History.Treeview",
                        background="#2c3e50", foreground="white",
                        fieldbackground="#2c3e50", borderwidth=0,
                        font=('Arial', 10), rowheight=30)
        style.map('History.Treeview', background=[('selected', '#3498db')])

        style.configure("History.Treeview.Heading",
                        background="#34495e", foreground="white",
                        borderwidth=1, font=('Arial', 11, 'bold'))

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1a1a2e")
        header.pack(fill=tk.X, pady=10)

        tk.Label(header, text="🚀 Advanced Cache Simulator with Analysis",
                 font=("Arial", 28, "bold"), bg="#1a1a2e", fg="#4ecdc4").pack()
        tk.Label(header, text="Complete Memory & Cache Visualization with Performance Analysis",
                 font=("Arial", 11), bg="#1a1a2e", fg="#95a5a6").pack()

        # Main container with paned window for resizing
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1a1a2e", sashwidth=8, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left - Controls
        left = tk.Frame(main_paned, bg="#2c3e50", width=300)
        main_paned.add(left)
        self.create_controls(left)

        # Center - Visualization and Analysis
        center_notebook = ttk.Notebook(main_paned)
        main_paned.add(center_notebook)

        # Visualization Tab
        vis_frame = tk.Frame(center_notebook, bg="#1a1a2e")
        center_notebook.add(vis_frame, text="🎬 Visualization")
        self.create_visualization(vis_frame)

        # Analysis Tab
        analysis_frame = tk.Frame(center_notebook, bg="#2c3e50")
        center_notebook.add(analysis_frame, text="📊 Analysis")
        self.analysis_tab = AnalysisTab(analysis_frame)

        # Right - History
        right = tk.Frame(main_paned, bg="#2c3e50", width=350)
        main_paned.add(right)
        self.create_history(right)

    def create_controls(self, parent):
        tk.Label(parent, text="⚙ CONTROLS", font=("Arial", 13, "bold"),
                 bg="#2c3e50", fg="#4ecdc4").pack(pady=10)

        # Request input
        tk.Label(parent, text="Request Sequence:", font=("Arial", 10, "bold"),
                 bg="#2c3e50", fg="#ecf0f1").pack(pady=(10, 4), padx=10, anchor=tk.W)
        self.entry_requests = tk.Text(parent, height=3, width=28, font=("Arial", 10),
                                      bg="#34495e", fg="white", insertbackground="white",
                                      relief=tk.FLAT, bd=5, wrap=tk.WORD)
        self.entry_requests.insert("1.0", "1 2 3 4 1 2 3 5 6 7")
        self.entry_requests.pack(padx=10, pady=5)

        # Cache size
        tk.Label(parent, text="Cache Size:", font=("Arial", 10, "bold"),
                 bg="#2c3e50", fg="#ecf0f1").pack(pady=(10, 4), padx=10, anchor=tk.W)
        self.entry_size = tk.Entry(parent, width=28, font=("Arial", 10),
                                   bg="#34495e", fg="white", insertbackground="white",
                                   relief=tk.FLAT, bd=5)
        self.entry_size.insert(0, "4")
        self.entry_size.pack(padx=10, pady=5)

        # Algorithm selection
        tk.Label(parent, text="Algorithm:", font=("Arial", 10, "bold"),
                 bg="#2c3e50", fg="#ecf0f1").pack(pady=(10, 4), padx=10, anchor=tk.W)

        self.algo_var = tk.StringVar(value="LRU")
        for algo in self.algorithms.keys():
            tk.Radiobutton(parent, text=algo, variable=self.algo_var, value=algo,
                           bg="#2c3e50", fg="white", selectcolor="#34495e",
                           activebackground="#2c3e50", activeforeground="#4ecdc4",
                           font=("Arial", 9), command=self.show_desc).pack(anchor=tk.W, padx=20, pady=2)

        self.desc_label = tk.Label(parent, text=self.algo_descriptions["LRU"],
                                   font=("Arial", 9), bg="#34495e", fg="#ecf0f1",
                                   wraplength=240, justify=tk.LEFT, relief=tk.FLAT, padx=8, pady=8)
        self.desc_label.pack(padx=10, pady=8, fill=tk.X)

        # Speed control
        tk.Label(parent, text="Speed:", font=("Arial", 10, "bold"),
                 bg="#2c3e50", fg="#ecf0f1").pack(pady=(8, 3), padx=10, anchor=tk.W)
        self.speed_scale = tk.Scale(parent, from_=3, to=1, orient=tk.HORIZONTAL,
                                    bg="#2c3e50", fg="white", troughcolor="#34495e",
                                    highlightthickness=0, command=self.update_speed)
        self.speed_scale.set(2)
        self.speed_scale.pack(padx=10, fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(parent, bg="#2c3e50")
        btn_frame.pack(pady=15)

        self.btn_start = tk.Button(btn_frame, text="▶ START", command=self.start,
                                   bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        self.btn_start.pack(pady=4, fill=tk.X)

        self.btn_compare = tk.Button(btn_frame, text="⚖ COMPARE ALL", command=self.compare_all,
                                     bg="#9b59b6", fg="white", font=("Arial", 11, "bold"),
                                     relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        self.btn_compare.pack(pady=4, fill=tk.X)

        self.btn_pause = tk.Button(btn_frame, text="⏸ PAUSE", command=self.pause,
                                   bg="#f39c12", fg="white", font=("Arial", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8, cursor="hand2", state=tk.DISABLED)
        self.btn_pause.pack(pady=4, fill=tk.X)

        self.btn_reset = tk.Button(btn_frame, text="↻ RESET", command=self.reset,
                                   bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        self.btn_reset.pack(pady=4, fill=tk.X)

        # Statistics
        tk.Label(parent, text="📊 REAL-TIME STATS", font=("Arial", 11, "bold"),
                 bg="#2c3e50", fg="#4ecdc4").pack(pady=(15, 8))

        self.stats_frame = tk.Frame(parent, bg="#34495e", relief=tk.FLAT, bd=3)
        self.stats_frame.pack(padx=10, pady=5, fill=tk.X)

        self.stats_labels = {}
        for stat in ["Hits", "Misses", "Hit Rate", "Progress"]:
            frame = tk.Frame(self.stats_frame, bg="#34495e")
            frame.pack(fill=tk.X, padx=6, pady=3)
            tk.Label(frame, text=f"{stat}:", font=("Arial", 9, "bold"),
                     bg="#34495e", fg="#bdc3c7").pack(side=tk.LEFT)
            label = tk.Label(frame, text="0", font=("Arial", 9, "bold"),
                             bg="#34495e", fg="white")
            label.pack(side=tk.RIGHT)
            self.stats_labels[stat] = label

    def create_visualization(self, parent):
        self.canvas = AnimatedCacheVisualizer(parent, bg="#1a1a2e",
                                              highlightthickness=0, height=420)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(parent, text="Ready to simulate",
                                     font=("Arial", 10, "bold"), bg="#2c3e50", fg="#4ecdc4",
                                     relief=tk.FLAT, pady=10)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def create_history(self, parent):
        tk.Label(parent, text="📋 EXECUTION HISTORY", font=("Arial", 12, "bold"),
                 bg="#2c3e50", fg="#4ecdc4").pack(pady=10)

        table_frame = tk.Frame(parent, bg="#2c3e50")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)

        self.history_table = ttk.Treeview(
            table_frame, columns=("Step", "Request", "Action", "Cache"),
            show="headings", style="History.Treeview",
            yscrollcommand=scrollbar.set, height=12
        )

        scrollbar.config(command=self.history_table.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_table.heading("Step", text="STEP")
        self.history_table.heading("Request", text="REQ")
        self.history_table.heading("Action", text="ACTION")
        self.history_table.heading("Cache", text="CACHE")

        self.history_table.column("Step", width=45, anchor=tk.CENTER)
        self.history_table.column("Request", width=45, anchor=tk.CENTER)
        self.history_table.column("Action", width=90, anchor=tk.CENTER)
        self.history_table.column("Cache", width=150, anchor=tk.W)

        self.history_table.pack(fill=tk.BOTH, expand=True)

        self.history_table.tag_configure('hit', background='#27ae60', foreground='white')
        self.history_table.tag_configure('miss', background='#c0392b', foreground='white')

        tk.Label(parent, text="📝 EVENT LOG", font=("Arial", 11, "bold"),
                 bg="#2c3e50", fg="#f39c12").pack(pady=(15, 5))

        log_frame = tk.Frame(parent, bg="#2c3e50")
        log_frame.pack(fill=tk.BOTH, padx=10, pady=5)

        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.event_log = tk.Listbox(log_frame, bg="#34495e", fg="white",
                                    font=("Courier", 9), selectbackground="#3498db",
                                    relief=tk.FLAT, bd=0, height=8,
                                    yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.event_log.yview)
        self.event_log.pack(fill=tk.BOTH, expand=True)

    def show_desc(self):
        self.desc_label.config(text=self.algo_descriptions[self.algo_var.get()])

    def update_speed(self, value):
        self.animation_speed = {1: 700, 2: 1000, 3: 1600}[int(float(value))]

    def add_log(self, msg, color="white"):
        self.event_log.insert(tk.END, msg)
        self.event_log.itemconfig(tk.END, fg=color)
        self.event_log.see(tk.END)

    def start(self):
        if self.is_running:
            return

        try:
            reqs = list(map(int, self.entry_requests.get("1.0", tk.END).split()))
            size = int(self.entry_size.get())
            if size < 1 or len(reqs) == 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid input!")
            return

        algo = self.algo_var.get()
        self.current_results = self.algorithms[algo](reqs, size)
        self.current_step = 0
        self.is_running = True

        # Store results for analysis
        self.all_algorithm_results[algo] = self.current_results

        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)

        for item in self.history_table.get_children():
            self.history_table.delete(item)
        self.event_log.delete(0, tk.END)

        self.canvas.initialize_visualization(size, reqs)

        self.add_log("▶ Simulation Started", "#4ecdc4")
        self.add_log(f"Algorithm: {algo}", "#95a5a6")
        self.add_log(f"Cache Size: {size}", "#95a5a6")
        self.add_log(f"Requests: {len(reqs)}", "#95a5a6")
        self.add_log("-" * 35, "#555")

        # Update analysis tab
        self.analysis_tab.update_analysis(self.current_results, algo, reqs, size)

        self.animate_next()

    def compare_all(self):
        """Run all algorithms and compare results"""
        try:
            reqs = list(map(int, self.entry_requests.get("1.0", tk.END).split()))
            size = int(self.entry_size.get())
            if size < 1 or len(reqs) == 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid input!")
            return

        # Clear previous results
        self.all_algorithm_results = {}

        # Run all algorithms
        for algo_name, algo_func in self.algorithms.items():
            results = algo_func(reqs, size)
            self.all_algorithm_results[algo_name] = results

            # Log each algorithm's performance
            hits = sum(1 for r in results if r[1] == "HIT")
            hit_rate = (hits / len(results) * 100) if results else 0
            self.add_log(f"{algo_name}: {hit_rate:.1f}% hit rate",
                         "#2ecc71" if hit_rate > 50 else "#e74c3c")

        # Update comparison tab
        self.analysis_tab.update_comparison(self.all_algorithm_results)

        # Show summary
        best_algo = max(self.all_algorithm_results.items(),
                        key=lambda x: sum(1 for r in x[1] if r[1] == "HIT"))
        best_hits = sum(1 for r in best_algo[1] if r[1] == "HIT")
        best_rate = (best_hits / len(best_algo[1]) * 100)

        self.add_log(f"🏆 Best: {best_algo[0]} ({best_rate:.1f}%)", "#f39c12")
        self.add_log("⚖ Comparison complete!", "#9b59b6")

    def animate_next(self):
        if not self.is_running or self.current_step >= len(self.current_results):
            self.finish()
            return

        step = self.current_results[self.current_step]
        req, action, cache, replaced = step

        self.status_label.config(text=f"Processing: {req} | {action}")

        hits = sum(1 for s in self.current_results[:self.current_step + 1] if s[1] == "HIT")
        misses = self.current_step + 1 - hits
        rate = (hits / (self.current_step + 1) * 100) if (self.current_step + 1) > 0 else 0

        self.stats_labels["Hits"].config(text=str(hits))
        self.stats_labels["Misses"].config(text=str(misses))
        self.stats_labels["Hit Rate"].config(text=f"{rate:.1f}%")
        self.stats_labels["Progress"].config(text=f"{self.current_step + 1}/{len(self.current_results)}")

        # Add to history table
        tag = 'hit' if action == 'HIT' else 'miss'
        cache_str = " ".join([f"[{c}]" for c in cache])
        item_id = self.history_table.insert("", "end",
                                            values=(self.current_step + 1, req, action, cache_str),
                                            tags=(tag,))
        self.history_table.see(item_id)

        # Add to event log
        if action == "HIT":
            self.add_log(f"Step {self.current_step + 1}: HIT {req}", "#2ecc71")
        else:
            if replaced:
                self.add_log(f"Step {self.current_step + 1}: MISS {req}, replaced {replaced}", "#e74c3c")
            else:
                self.add_log(f"Step {self.current_step + 1}: MISS {req}, added", "#e74c3c")

        self.canvas.animate_request(req, action, cache, replaced, self.after_anim)

    def after_anim(self):
        self.current_step += 1
        if self.is_running:
            self.root.after(self.animation_speed, self.animate_next)

    def pause(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL, text="▶ RESUME")
        self.btn_pause.config(state=tk.DISABLED)
        self.status_label.config(text="Paused")
        self.add_log("⏸ Paused", "#f39c12")

    def reset(self):
        self.is_running = False
        self.current_step = 0
        self.current_results = []
        self.all_algorithm_results = {}

        self.btn_start.config(state=tk.NORMAL, text="▶ START")
        self.btn_pause.config(state=tk.DISABLED)

        self.canvas.delete("all")
        self.status_label.config(text="Ready to simulate")

        for label in self.stats_labels.values():
            label.config(text="0")

        for item in self.history_table.get_children():
            self.history_table.delete(item)
        self.event_log.delete(0, tk.END)

        self.add_log("↻ Reset Complete", "#e74c3c")

    def finish(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL, text="▶ START")
        self.btn_pause.config(state=tk.DISABLED)
        self.status_label.config(text="✅ Simulation Complete!")
        self.add_log("✅ Simulation Complete!", "#2ecc71")

        # Calculate final statistics
        if self.current_results:
            total = len(self.current_results)
            hits = sum(1 for r in self.current_results if r[1] == "HIT")
            hit_rate = (hits / total * 100)
            self.add_log(f"Final Hit Rate: {hit_rate:.2f}%", "#4ecdc4")
            self.add_log(f"Total Hits: {hits}, Total Misses: {total - hits}", "#95a5a6")


if __name__ == "__main__":
    root = tk.Tk()
    app = CacheSimulatorApp(root)
    root.mainloop()