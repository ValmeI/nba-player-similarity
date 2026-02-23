import html

import streamlit as st


def _render_avatar(role: str) -> str:
    """Return an HTML avatar circle for the given role."""
    if role == "user":
        return '''<div style="width:36px; height:36px; border-radius:50%; background:#C9082A;
                    display:flex; align-items:center; justify-content:center; flex-shrink:0;
                    font-size:16px; box-shadow:0 1px 4px rgba(0,0,0,0.12);">\U0001f464</div>'''
    else:
        return '''<div style="width:36px; height:36px; border-radius:50%; background:#17408B;
                    display:flex; align-items:center; justify-content:center; flex-shrink:0;
                    font-size:16px; box-shadow:0 1px 4px rgba(0,0,0,0.12);">\U0001f3c0</div>'''


def display_chat_messages() -> None:
    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg["content"]
        is_html = msg.get("type") == "html"

        if is_html:
            st.html(content)
            chart = msg.get("chart")
            if chart:
                st.markdown(chart, unsafe_allow_html=True)
        else:
            escaped = html.escape(content)
            escaped = escaped.replace("\n", "<br>")
            avatar = _render_avatar(role)

            if role == "user":
                bubble_html = f'''
                <div style="display:flex; justify-content:flex-end; align-items:flex-start; gap:10px; margin:0.6rem 0;">
                    <div style="background:#17408B; color:#fff; border-radius:16px 4px 16px 16px;
                                padding:0.8rem 1.1rem; max-width:70%; font-size:0.95rem;
                                box-shadow:0 2px 8px rgba(23,64,139,0.2); line-height:1.5;">
                        {escaped}
                    </div>
                    {avatar}
                </div>'''
            else:
                bubble_html = f'''
                <div style="display:flex; justify-content:flex-start; align-items:flex-start; gap:10px; margin:0.6rem 0;">
                    {avatar}
                    <div style="background:#ffffff; color:#1a202c; border:1px solid #e2e8f0;
                                border-radius:4px 16px 16px 16px; padding:0.8rem 1.1rem;
                                max-width:70%; font-size:0.95rem;
                                box-shadow:0 1px 4px rgba(0,0,0,0.05); line-height:1.5;">
                        {escaped}
                    </div>
                </div>'''

            st.markdown(bubble_html, unsafe_allow_html=True)


def _inches_to_display(inches: int) -> str:
    if not inches:
        return "N/A"
    feet = inches // 12
    remaining = inches % 12
    return f"{feet}'{remaining}\""


def format_stats_for_display(user_stats: list[dict], similar_player_stats: list[dict], llm_summary: str, position: str | None = None, era: str | None = None) -> str:
    active_filters = []
    if position:
        active_filters.append(f"Position: {position}")
    if era:
        active_filters.append(f"Era: {era}")

    def similarity_class(score):
        return "nba-similarity-high" if score >= 98 else "nba-similarity-mid"

    filter_badges = ''.join(
        f'<span class="nba-filter-badge">{html.escape(f)}</span>' for f in active_filters
    ) if active_filters else ""
    filter_html_styled = f"<p>{filter_badges}</p>" if filter_badges else ""

    escaped_heading_name = html.escape(user_stats[0]['player_name'])
    escaped_llm_summary = html.escape(llm_summary)

    html_content = f"""
        <div class="nba-results-card">
        <h2>Players similar to {escaped_heading_name}</h2>
        {filter_html_styled}
        <h3>{escaped_heading_name} Career Stats</h3>
        <table class="nba-table">
            <tr>
                <th>Player</th>
                <th>Position</th>
                <th>Height</th>
                <th>Weight</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting %</th>
                <th>Field Goal %</th>
                <th>3 Point %</th>
                <th>Free Throw %</th>
                <th>Last Season</th>
                <th>Last Age</th>
                <th>Total Seasons</th>
            </tr>
            {''.join([
                f'<tr><td>{html.escape(str(player["player_name"]))}</td>'
                f'<td>{html.escape(str(player["position"]))}</td>'
                f'<td>{_inches_to_display(player.get("height_inches", 0))}</td>'
                f'<td>{player.get("weight", 0)} lbs</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.1f}%</td>'
                f'<td>{player["field_goal_percentage"]:.1f}%</td>'
                f'<td>{player["three_point_percentage"]:.1f}%</td>'
                f'<td>{player["free_throw_percentage"]:.1f}%</td>'
                f'<td>{html.escape(str(player["last_played_season"]))}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td></tr>'
                for player in user_stats
            ])}
        </table>
        <h3>Similar Players</h3>
        <table class="nba-table">
            <tr>
                <th>Player</th>
                <th>Position</th>
                <th>Height</th>
                <th>Weight</th>
                <th>Points/Game</th>
                <th>Assists/Game</th>
                <th>Rebounds/Game</th>
                <th>Blocks/Game</th>
                <th>Steals/Game</th>
                <th>True Shooting %</th>
                <th>Field Goal %</th>
                <th>3 Point %</th>
                <th>Free Throw %</th>
                <th>Last Season</th>
                <th>Last Age</th>
                <th>Total Seasons</th>
                <th>Similarity</th>
            </tr>
            {''.join([
                f'<tr><td>{html.escape(str(player["player_name"]))}</td>'
                f'<td>{html.escape(str(player["position"]))}</td>'
                f'<td>{_inches_to_display(player.get("height_inches", 0))}</td>'
                f'<td>{player.get("weight", 0)} lbs</td>'
                f'<td>{player["points_per_game"]}</td>'
                f'<td>{player["assists_per_game"]}</td>'
                f'<td>{player["rebounds_per_game"]}</td>'
                f'<td>{player["blocks_per_game"]}</td>'
                f'<td>{player["steals_per_game"]}</td>'
                f'<td>{player["true_shooting_percentage"]:.1f}%</td>'
                f'<td>{player["field_goal_percentage"]:.1f}%</td>'
                f'<td>{player["three_point_percentage"]:.1f}%</td>'
                f'<td>{player["free_throw_percentage"]:.1f}%</td>'
                f'<td>{html.escape(str(player["last_played_season"]))}</td>'
                f'<td>{player["last_played_age"]}</td>'
                f'<td>{player["total_seasons"]}</td>'
                f'<td class="{similarity_class(player["similarity_score"])}">{player["similarity_score"]:.1f}%</td></tr>'
                for player in similar_player_stats
            ])}
        </table>
        <h3>Analysis</h3>
        <div class="nba-summary">{escaped_llm_summary}</div>
        </div>
    """
    return html_content


def inject_nba_theme() -> None:
    """Inject global NBA-themed CSS."""
    st.markdown("""
    <style>
        /* === Font === */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* === Page background === */
        .stApp {
            background-color: #f4f4f4;
        }
        .block-container {
            padding-top: 1rem !important;
        }

        /* === Header banner === */
        .nba-header {
            background: linear-gradient(135deg, #17408B 0%, #1a4fa0 50%, #17408B 100%);
            padding: 2rem 1.5rem 1.2rem 1.5rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px rgba(23, 64, 139, 0.35);
        }
        .nba-header h1 {
            color: #ffffff !important;
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .nba-header .nba-subtitle {
            color: rgba(255, 255, 255, 0.85) !important;
            font-size: 1rem;
            margin: 0.3rem 0 0 0;
        }
        .nba-header .nba-version {
            color: rgba(255, 255, 255, 0.45) !important;
            font-size: 0.72rem;
            margin: 0.6rem 0 0 0;
        }


        /* === Input styling === */
        .stTextInput label {
            font-weight: 600;
            color: #17408B;
        }
        .stTextInput input {
            border: 2px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            background: #ffffff !important;
        }
        .stTextInput input:focus {
            border-color: #17408B !important;
            box-shadow: 0 0 0 3px rgba(23, 64, 139, 0.12) !important;
        }
        /* Kill Streamlit's default focus wrapper border */
        .stTextInput div[data-baseweb] {
            border: none !important;
            box-shadow: none !important;
        }
        .stTextInput input::placeholder {
            color: #a0aec0;
        }

        /* === Scrollbar === */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #17408B; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #C9082A; }

        /* === Footer === */
        .nba-footer {
            text-align: center;
            color: #a0aec0;
            font-size: 0.78rem;
            padding: 1.5rem 0 0.5rem 0;
            border-top: 1px solid #e2e8f0;
            margin-top: 2rem;
        }

        /* === Hide Streamlit chrome === */
        #MainMenu, .stDeployButton, [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
            display: none !important;
        }
        header[data-testid="stHeader"] { display: none !important; }
        footer { visibility: hidden; }

        /* === NBA Results Card (used by format_stats_for_display) === */
        .nba-results-card { background:#fff; border-radius:12px; padding:24px 28px; box-shadow:0 2px 12px rgba(0,0,0,0.07); }
        .nba-results-card h2 { color:#17408B; font-size:1.5rem; font-weight:700; margin:0 0 4px 0; border-bottom:3px solid #C9082A; padding-bottom:10px; display:inline-block; }
        .nba-results-card h3 { color:#2d3748; font-size:1.1rem; font-weight:600; margin:20px 0 8px 0; }
        .nba-table { border-collapse:collapse; width:100%; font-size:13px; margin:8px 0 16px 0; box-shadow:0 1px 6px rgba(0,0,0,0.06); border-radius:8px; overflow:hidden; }
        .nba-table th { background:linear-gradient(180deg,#C9082A 0%,#a8061f 100%); color:#fff; padding:10px; text-align:center; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.3px; border:none; white-space:nowrap; }
        .nba-table td { padding:9px 10px; text-align:center; border-bottom:1px solid #edf2f7; color:#2d3748; }
        .nba-table tr:nth-child(even) { background:#fafbfc; }
        .nba-table tr:hover { background:#edf2f7; }
        .nba-table td:first-child { text-align:left; font-weight:600; color:#17408B; }
        .nba-filter-badge { display:inline-block; background:linear-gradient(135deg,#17408B,#1a4fa0); color:#fff; padding:4px 14px; border-radius:16px; font-size:12px; font-weight:500; margin:2px 4px; }
        .nba-similarity-high { color:#276749; font-weight:700; background:#f0fff4; padding:2px 8px; border-radius:10px; }
        .nba-similarity-mid { color:#C9082A; font-weight:600; background:#fff5f5; padding:2px 8px; border-radius:10px; }
        .nba-summary { background:linear-gradient(135deg,#f7fafc 0%,#edf2f7 100%); border-left:4px solid #17408B; padding:18px 20px; margin:16px 0 0 0; border-radius:0 10px 10px 0; line-height:1.7; font-size:14px; color:#2d3748; }
    </style>
    """, unsafe_allow_html=True)
