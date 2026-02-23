import html
import math


def generate_radar_chart_html(user_stats, similar_player_stats):
    """Generate a pure SVG radar chart comparing the searched player vs top similar players."""
    if not similar_player_stats:
        return ""

    axes = [
        ("PPG", "points_per_game", 0, 35),
        ("APG", "assists_per_game", 0, 12),
        ("RPG", "rebounds_per_game", 0, 15),
        ("SPG", "steals_per_game", 0, 3),
        ("BPG", "blocks_per_game", 0, 4),
        ("TS%", "true_shooting_percentage", 0, 100),
        ("FG%", "field_goal_percentage", 0, 70),
        ("3P%", "three_point_percentage", 0, 50),
    ]

    n = len(axes)
    cx, cy = 250, 250
    max_r = 180
    angles = [(-math.pi / 2 + 2 * math.pi * i / n) for i in range(n)]

    def to_xy(angle, r):
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    def normalize(val, lo, hi):
        if val is None:
            return 0
        return min(max((val - lo) / (hi - lo), 0), 1)

    def raw_val(player, key):
        v = player.get(key)
        return round(v, 1) if v is not None else 0

    # Grid polygons at 25%, 50%, 75%, 100%
    grid = []
    for pct in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * pct
        pts = " ".join(f"{to_xy(a, r)[0]:.1f},{to_xy(a, r)[1]:.1f}" for a in angles)
        grid.append(f'<polygon points="{pts}" fill="none" stroke="#e2e8f0" stroke-width="1"/>')

    # Axis spokes
    spokes = []
    for a in angles:
        ex, ey = to_xy(a, max_r)
        spokes.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#e2e8f0" stroke-width="1"/>')

    # Axis labels
    axis_labels = []
    for i, (label, _, _, _) in enumerate(axes):
        lx, ly = to_xy(angles[i], max_r + 22)
        anchor = "middle"
        if lx < cx - 10:
            anchor = "end"
        elif lx > cx + 10:
            anchor = "start"
        axis_labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="12" font-weight="600" fill="#4a5568">{label}</text>'
        )

    # Player polygons + dots
    colors = [
        ("#17408B", "rgba(23,64,139,0.22)"),
        ("#C9082A", "rgba(201,8,42,0.16)"),
        ("#1D8348", "rgba(29,131,72,0.16)"),
        ("#F39C12", "rgba(243,156,18,0.16)"),
    ]
    all_players = [user_stats[0]] + similar_player_stats[:3]
    polys = []
    dots = []
    for pi, player in enumerate(all_players):
        stroke, fill = colors[pi]
        pts = []
        for i, (label, key, lo, hi) in enumerate(axes):
            norm = normalize(player.get(key), lo, hi)
            px, py = to_xy(angles[i], max_r * norm)
            pts.append((px, py, raw_val(player, key), label))
        points_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)
        polys.append(f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        for px, py, raw, label in pts:
            dots.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{stroke}" '
                f'stroke="#fff" stroke-width="1.5"/>'
            )

    # Legend (HTML for proper text layout)
    legend_items = []
    for pi, player in enumerate(all_players):
        stroke, _ = colors[pi]
        name = html.escape(player["player_name"])
        legend_items.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#2d3748;">'
            f'<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:{stroke};flex-shrink:0;"></span>'
            f'{name}</span>'
        )
    legend_html = (
        '<div style="display:flex;justify-content:center;gap:18px;flex-wrap:wrap;margin-top:6px;">'
        + "".join(legend_items) + '</div>'
    )

    svg_parts = "\n".join(grid + spokes + axis_labels + polys + dots)
    return f"""
    <div style="max-width:500px;margin:20px auto 8px auto;text-align:center;">
        <svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg"
             style="display:block;width:100%;max-width:500px;margin:0 auto;">
            {svg_parts}
        </svg>
        {legend_html}
    </div>
    """
