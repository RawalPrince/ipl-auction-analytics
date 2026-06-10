import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import sqlite3

# ── Global Theme ──────────────────────────────────────
pio.templates["dark_custom"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0", size=12),
        xaxis=dict(gridcolor="#2a2a3e", linecolor="#444",
                   tickcolor="#e0e0e0", color="#e0e0e0"),
        yaxis=dict(gridcolor="#2a2a3e", linecolor="#444",
                   tickcolor="#e0e0e0", color="#e0e0e0"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#444",
                    font=dict(color="#e0e0e0"))
    )
)
pio.templates.default = "dark_custom"

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────
@st.cache_data
def load_data():
    conn       = sqlite3.connect("data/processed/ipl.db")
    matches    = pd.read_sql("SELECT * FROM matches", conn)
    deliveries = pd.read_sql("SELECT * FROM deliveries", conn)
    auction    = pd.read_sql("SELECT * FROM auction", conn)
    conn.close()

    matches["date"] = pd.to_datetime(matches["date"])
    return matches, deliveries, auction

matches, deliveries, auction = load_data()

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/634/634012.png", width=60)
    st.title("IPL Analytics\nDashboard")
    st.markdown("---")

    all_seasons = sorted(matches["season"].unique())
    selected_seasons = st.multiselect(
        "Filter by Season:",
        options=all_seasons,
        default=all_seasons
    )

    st.markdown("---")
    st.markdown(f"**Matches:** {len(matches):,}")
    st.markdown(f"**Deliveries:** {len(deliveries):,}")
    st.markdown(f"**Seasons:** {len(all_seasons)}")
    st.markdown("---")
    st.markdown("Built by **Prince Rawal**")
    st.markdown("B.E. Computer Engineering")
    st.markdown("Python | SQL | Streamlit")

# ── Apply Season Filter ───────────────────────────────
matches_f    = matches[matches["season"].isin(selected_seasons)]
deliveries_f = deliveries[deliveries["season"].isin(selected_seasons)]

# ── Title ─────────────────────────────────────────────
st.title("🏏 IPL Player & Match Analytics")
st.markdown(f"**{len(matches_f):,} matches | {len(deliveries_f):,} deliveries | "
            f"Seasons: {min(selected_seasons)} – {max(selected_seasons)}**")
st.markdown("---")

# ── Metric Cards ──────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Matches",    f"{len(matches_f):,}")
c2.metric("Total Deliveries", f"{len(deliveries_f):,}")
c3.metric("Unique Batters",   f"{deliveries_f['batter'].nunique():,}")
c4.metric("Unique Bowlers",   f"{deliveries_f['bowler'].nunique():,}")
c5.metric("Seasons",          f"{len(selected_seasons)}")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Team Performance",
    "🏏 Batting Stats",
    "🎳 Bowling Stats",
    "💰 Auction Analysis",
    "🏟️ Venue & Toss"
])

# ════════════════════════════════════════════════════
# TAB 1 — TEAM PERFORMANCE
# ════════════════════════════════════════════════════
with tab1:
    st.subheader("Team Performance Analysis")

    # Total wins per team
    team_wins = matches_f[
        matches_f["winner"].notna() &
        (matches_f["winner"] != "NA")
    ]["winner"].value_counts().reset_index()
    team_wins.columns = ["team", "wins"]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            team_wins.head(10),
            x="wins", y="team",
            orientation="h",
            title="Most Wins — All Time",
            color="wins",
            color_continuous_scale="Blues",
            text="wins"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=420, showlegend=False,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            yaxis=dict(categoryorder="total ascending")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Win % including matches played
        team_played = pd.concat([
            matches_f["team1"], matches_f["team2"]
        ]).value_counts().reset_index()
        team_played.columns = ["team", "played"]

        team_stats = team_wins.merge(team_played, on="team")
        team_stats["win_pct"] = (
            team_stats["wins"] / team_stats["played"] * 100
        ).round(1)
        team_stats = team_stats.sort_values("win_pct", ascending=False).head(10)

        fig2 = px.bar(
            team_stats,
            x="win_pct", y="team",
            orientation="h",
            title="Win Percentage by Team",
            color="win_pct",
            color_continuous_scale="Greens",
            text="win_pct"
        )
        fig2.update_traces(textposition="outside",
                           texttemplate="%{text}%")
        fig2.update_layout(
            height=420, showlegend=False,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            yaxis=dict(categoryorder="total ascending")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Season-wise wins heatmap
    season_wins = matches_f[
        matches_f["winner"].notna() &
        (matches_f["winner"] != "NA")
    ].groupby(["season", "winner"]).size().reset_index()
    season_wins.columns = ["season", "team", "wins"]

    pivot = season_wins.pivot(
        index="team", columns="season", values="wins"
    ).fillna(0)

    fig3 = px.imshow(
        pivot,
        title="Team Wins per Season — Heatmap",
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig3.update_layout(
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0")
    )
    st.plotly_chart(fig3, use_container_width=True)

# ════════════════════════════════════════════════════
# TAB 2 — BATTING STATS
# ════════════════════════════════════════════════════
with tab2:
    st.subheader("Batting Performance Analysis")

    # Compute batting stats
    batting = deliveries_f[deliveries_f["is_legal"] == True].groupby("batter").agg(
        total_runs   = ("batsman_runs", "sum"),
        balls_faced  = ("batsman_runs", "count"),
        matches      = ("match_id", "nunique"),
        fours        = ("is_four", "sum"),
        sixes        = ("is_six", "sum"),
        is_wicket    = ("is_wicket", "sum")
    ).reset_index()

    batting["strike_rate"]   = (batting["total_runs"] / batting["balls_faced"] * 100).round(2)
    batting["boundary_pct"]  = ((batting["fours"] + batting["sixes"]) / batting["balls_faced"] * 100).round(2)
    batting["avg"]           = (batting["total_runs"] / batting["is_wicket"].replace(0,1)).round(2)
    batting = batting[batting["matches"] >= 20].sort_values("total_runs", ascending=False)

    top_n = st.slider("Show top N batsmen:", 5, 30, 15)
    top_bat = batting.head(top_n)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            top_bat, x="batter", y="total_runs",
            title=f"Top {top_n} Run Scorers",
            color="strike_rate",
            color_continuous_scale="Oranges",
            text="total_runs"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=420,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(
            batting.head(50),
            x="strike_rate", y="total_runs",
            size="matches", color="boundary_pct",
            hover_name="batter",
            title="Strike Rate vs Total Runs (top 50)",
            color_continuous_scale="Viridis",
            labels={"strike_rate": "Strike Rate",
                    "total_runs": "Total Runs"}
        )
        fig2.update_layout(
            height=420,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Sixes leaderboard
    six_leaders = batting.nlargest(15, "sixes")[
        ["batter","sixes","fours","total_runs","matches"]
    ]
    st.subheader("💥 Six Hitters Leaderboard")
    fig3 = px.bar(
        six_leaders, x="batter", y="sixes",
        title="Most Sixes in IPL History",
        color="sixes", color_continuous_scale="Reds",
        text="sixes"
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(
        height=380,
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig3, use_container_width=True)

# ════════════════════════════════════════════════════
# TAB 3 — BOWLING STATS
# ════════════════════════════════════════════════════
with tab3:
    st.subheader("Bowling Performance Analysis")

    bowling = deliveries_f[deliveries_f["is_legal"] == True].groupby("bowler").agg(
        wickets  = ("is_wicket", "sum"),
        runs     = ("total_runs", "sum"),
        balls    = ("total_runs", "count"),
        matches  = ("match_id", "nunique")
    ).reset_index()

    bowling["economy"] = (bowling["runs"] / bowling["balls"] * 6).round(2)
    bowling["bowling_sr"] = (bowling["balls"] / bowling["wickets"].replace(0, np.nan)).round(2)
    bowling = bowling[bowling["matches"] >= 20].sort_values("wickets", ascending=False)

    top_n_bowl = st.slider("Show top N bowlers:", 5, 30, 15)
    top_bowl   = bowling.head(top_n_bowl)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            top_bowl, x="bowler", y="wickets",
            title=f"Top {top_n_bowl} Wicket Takers",
            color="economy",
            color_continuous_scale="Blues_r",
            text="wickets"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=420,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(
            bowling.head(50),
            x="economy", y="wickets",
            size="matches", color="bowling_sr",
            hover_name="bowler",
            title="Economy vs Wickets (top 50)",
            color_continuous_scale="RdYlGn_r",
            labels={"economy": "Economy Rate",
                    "wickets": "Total Wickets"}
        )
        fig2.update_layout(
            height=420,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0")
        )
        st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════
# TAB 4 — AUCTION ANALYSIS
# ════════════════════════════════════════════════════
with tab4:
    st.subheader("IPL Auction Analysis — 2022 & 2023")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Players Sold", f"{len(auction):,}")
    col2.metric("Total Spend (Cr)",
                f"₹{auction['sold_price_lakh'].sum()/100:.0f} Cr")
    col3.metric("Most Expensive",
                f"₹{auction['sold_price_lakh'].max()/100:.0f} Cr")
    col4.metric("Avg Price (Lakh)",
                f"₹{auction['sold_price_lakh'].mean():.0f}L")

    col1, col2 = st.columns(2)
    with col1:
        top_expensive = auction.nlargest(15, "sold_price_lakh")
        fig = px.bar(
            top_expensive,
            x="sold_price_lakh", y="player",
            orientation="h",
            title="Top 15 Most Expensive Players",
            color="season",
            text="sold_price_lakh",
            hover_data=["team","role"]
        )
        fig.update_traces(texttemplate="₹%{text:.0f}L",
                          textposition="outside")
        fig.update_layout(
            height=500,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            yaxis=dict(categoryorder="total ascending")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Team spend
        team_spend = auction.groupby(
            ["team","season"]
        )["sold_price_lakh"].sum().reset_index()
        team_spend.columns = ["team","season","total_spend"]

        fig2 = px.bar(
            team_spend.sort_values("total_spend", ascending=False),
            x="team", y="total_spend",
            color="season",
            title="Total Auction Spend by Team",
            barmode="group",
            text="total_spend"
        )
        fig2.update_traces(texttemplate="₹%{text:.0f}L",
                           textposition="outside")
        fig2.update_layout(
            height=500,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Value for money — price multiplier
    st.subheader("🎯 Biggest Price Jumps — Base vs Sold Price")
    value = auction[auction["price_multiplier"] < 100].nlargest(
        15, "price_multiplier"
    )
    fig3 = px.bar(
        value, x="player", y="price_multiplier",
        color="role",
        title="Price Multiplier (Sold Price / Base Price)",
        text="price_multiplier",
        hover_data=["team","sold_price_lakh","base_price_lakh","season"]
    )
    fig3.update_traces(texttemplate="%{text:.1f}x",
                       textposition="outside")
    fig3.update_layout(
        height=420,
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Role breakdown
    col1, col2 = st.columns(2)
    with col1:
        role_spend = auction.groupby("role")["sold_price_lakh"].sum().reset_index()
        fig4 = px.pie(
            role_spend, values="sold_price_lakh", names="role",
            title="Auction Spend by Player Role",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0")
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        country_spend = auction.groupby(
            "country"
        )["sold_price_lakh"].sum().reset_index()
        country_spend = country_spend.sort_values(
            "sold_price_lakh", ascending=False
        ).head(10)
        fig5 = px.bar(
            country_spend, x="country", y="sold_price_lakh",
            title="Auction Spend by Country",
            color="sold_price_lakh",
            color_continuous_scale="Purples"
        )
        fig5.update_layout(
            height=380,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig5, use_container_width=True)

# ════════════════════════════════════════════════════
# TAB 5 — VENUE & TOSS
# ════════════════════════════════════════════════════
with tab5:
    st.subheader("Venue & Toss Impact Analysis")

    # Toss impact
    toss = matches_f[
        matches_f["winner"].notna() &
        (matches_f["winner"] != "NA")
    ].copy()
    toss["toss_won_match"] = toss["toss_winner"] == toss["winner"]

    toss_summary = toss.groupby("toss_decision").agg(
        total        = ("toss_decision", "count"),
        toss_won_match = ("toss_won_match", "sum")
    ).reset_index()
    toss_summary["win_pct"] = (
        toss_summary["toss_won_match"] /
        toss_summary["total"] * 100
    ).round(1)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            toss_summary,
            x="toss_decision", y="win_pct",
            title="Win % After Toss Decision",
            color="toss_decision",
            text="win_pct",
            color_discrete_map={
                "bat":   "#2196F3",
                "field": "#4CAF50"
            }
        )
        fig.update_traces(texttemplate="%{text}%",
                          textposition="outside")
        fig.add_hline(y=50, line_dash="dash",
                      line_color="red",
                      annotation_text="50% baseline")
        fig.update_layout(
            height=400,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **Key Finding:** Teams winning toss and choosing "
                "to field win **53.86%** of matches vs 45.38% when batting first")

    with col2:
        toss_season = toss.groupby(
            ["season","toss_decision"]
        )["toss_won_match"].mean().reset_index()
        toss_season["win_pct"] = (
            toss_season["toss_won_match"] * 100
        ).round(1)

        fig2 = px.line(
            toss_season,
            x="season", y="win_pct",
            color="toss_decision",
            title="Toss Win % Trend by Season",
            markers=True,
            color_discrete_map={
                "bat":   "#2196F3",
                "field": "#4CAF50"
            }
        )
        fig2.add_hline(y=50, line_dash="dash", line_color="red")
        fig2.update_layout(
            height=400,
            plot_bgcolor="#1a1a2e",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Top venues
    venue_stats = matches_f.groupby("venue").agg(
        matches      = ("id", "count"),
        avg_target   = ("target_runs", "mean")
    ).reset_index().sort_values("matches", ascending=False).head(12)

    fig3 = px.bar(
        venue_stats,
        x="matches", y="venue",
        orientation="h",
        title="Most Used Venues",
        color="avg_target",
        color_continuous_scale="Oranges",
        text="matches"
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(
        height=500,
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        yaxis=dict(categoryorder="total ascending")
    )
    st.plotly_chart(fig3, use_container_width=True)