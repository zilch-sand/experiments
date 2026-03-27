"""
WEF Global Risk Reports - Animated Rank Charts

Creates animated bump charts showing how global risk rankings change over time.
Produces:
1. Short-term risks animation (Likelihood 2007-2021 → 2-year severity 2023-2026)
2. Long-term risks animation (Impact 2007-2021 → 10-year severity 2022-2026)
3. Long-term-to-short-term materialization analysis
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

from data import (
    TOP_LIKELIHOOD, TOP_IMPACT, TOP_SHORT_TERM, TOP_LONG_TERM,
    SEVERITY_10Y_2022, NORMALIZE, NORMALIZED_CATEGORIES,
    RISK_CATEGORIES
)

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Color scheme matching WEF report categories
CATEGORY_COLORS = {
    "Economic": "#3B7DD8",       # Blue
    "Environmental": "#4CAF50",  # Green
    "Geopolitical": "#FF9800",   # Orange
    "Societal": "#E91E63",       # Pink/Red
    "Technological": "#9C27B0",  # Purple
}

def get_category(risk_name):
    """Get category for a risk name."""
    if risk_name in RISK_CATEGORIES:
        return RISK_CATEGORIES[risk_name]
    norm = NORMALIZE.get(risk_name, risk_name)
    return NORMALIZED_CATEGORIES.get(norm, "Unknown")

def get_color(risk_name):
    """Get color for a risk based on its category."""
    cat = get_category(risk_name)
    return CATEGORY_COLORS.get(cat, "#999999")

def shorten_name(name, max_len=35):
    """Shorten risk name for display."""
    # Common shortenings
    shorts = {
        "Failure of climate-change mitigation and adaptation": "Climate change failure",
        "Failure to mitigate climate change": "Climate change failure",
        "Failure of climate-change adaptation": "Climate adaptation failure",
        "Breakdown of critical information infrastructure": "IT infrastructure breakdown",
        "Critical information infrastructure breakdown": "IT infrastructure breakdown",
        "Extreme volatility in energy and agriculture prices": "Energy/food price volatility",
        "Large-scale involuntary migration": "Involuntary migration",
        "Large-scale terrorist attacks": "Terrorist attacks",
        "Massive incident of data fraud/theft": "Data fraud/theft",
        "Failure of national governance": "Governance failure",
        "Global governance failure": "Governance failure",
        "Spread of infectious diseases": "Infectious diseases",
        "Biodiversity loss and ecosystem collapse": "Biodiversity loss",
        "Human-made environmental disasters": "Environmental damage",
        "Human environmental damage": "Environmental damage",
        "Natural disasters and extreme weather events": "Extreme weather / natural disasters",
        "Large-scale environmental damage incidents": "Environmental damage",
        "Widespread cybercrime and cyber insecurity": "Cyber insecurity",
        "Erosion of social cohesion and societal polarization": "Societal polarization",
        "Misinformation and disinformation": "Misinformation & disinformation",
        "Cyber espionage and warfare": "Cyber warfare",
        "State-based armed conflict": "Armed conflict",
        "Interstate armed conflict": "Interstate conflict",
        "Adverse outcomes of AI technologies": "AI risks",
        "Diffusion of weapons of mass destruction": "WMD proliferation",
        "Mismanagement of population ageing": "Population ageing",
        "Unemployment or underemployment": "Unemployment",
        "Lack of economic opportunity": "Lack of economic opportunity",
        "Erosion of human rights": "Erosion of human rights",
        "Retrenchment from globalization": "Deglobalization",
        "Natural resource crises": "Natural resource shortages",
        "Chronic fiscal imbalances": "Fiscal imbalances",
        "Major systemic financial failure": "Financial system failure",
        "Slowing Chinese economy": "China slowdown",
        "Cost-of-living crisis": "Cost-of-living crisis",
        "Critical change to Earth systems": "Earth systems change",
        "Concentration of strategic resources": "Strategic resource concentration",
        "Involuntary migration": "Involuntary migration",
        "Geoeconomic confrontation": "Geoeconomic confrontation",
        "Digital power concentration": "Digital power concentration",
        "Natural resource shortages": "Natural resource shortages",
        "Weapons of mass destruction": "Weapons of mass destruction",
        "Societal polarization": "Societal polarization",
        "Extreme weather events": "Extreme weather",
        "Cybersecurity failure": "Cybersecurity failure",
        "Interstate relations fracture": "Interstate relations fracture",
        "Social cohesion erosion": "Social cohesion erosion",
        "Interstate conflict": "Interstate conflict",
        "Geopolitical conflict": "Geopolitical conflict",
        "Asset price collapse": "Asset price collapse",
        "Biodiversity loss": "Biodiversity loss",
        "Extreme energy price volatility": "Energy price volatility",
        "Oil price spike": "Oil price spike",
        "Oil and gas price spike": "Oil/gas price spike",
        "Severe income disparity": "Income disparity",
        "Rising greenhouse gas emissions": "GHG emissions",
        "Water supply crises": "Water crises",
        "Food shortage crises": "Food crises",
        # Additional shortenings for ranks 11-34
        "Ineffectiveness of multilateral institutions and international cooperation": "Multilateral failure",
        "Collapse of a systemically important industry or supply chain": "Supply chain collapse",
        "Disruptions to a systemically important supply chain": "Supply chain disruption",
        "Severe mental health deterioration": "Mental health deterioration",
        "Breakdown of critical information infrastructure": "IT infrastructure breakdown",
        "State collapse or severe instability": "State collapse",
        "Chronic diseases and health conditions": "Chronic diseases",
        "Collapse or lack of public infrastructure and services": "Infrastructure failure",
        "Insufficient public infrastructure and services": "Infrastructure failure",
        "Insufficient public infrastructure and social protections": "Infrastructure failure",
        "Proliferation of illicit economic activity": "Illicit economic activity",
        "Digital inequality and lack of access to digital services": "Digital inequality",
        "Adverse outcomes of frontier technologies": "Frontier tech risks",
        "Failure to stabilize price trajectories": "Price instability",
        "Use of weapons of mass destruction": "WMD use",
        "Technological power concentration": "Tech power concentration",
        "Disruptions to critical infrastructure": "Infrastructure disruption",
        "Censorship and surveillance": "Censorship & surveillance",
        "Erosion of human rights and/or of civic freedoms": "Erosion of human rights",
        "Involuntary migration or displacement": "Involuntary migration",
        "Biological, chemical or nuclear hazards": "CBRN hazards",
        "Biological, chemical or nuclear weapons or hazards": "CBRN hazards",
        "Non-weather related natural disasters": "Non-weather disasters",
        "Concentration of strategic resources and technologies": "Strategic resource concentration",
        "Lack of economic opportunity or unemployment": "Lack of economic opportunity",
        "Talent and/or labour shortages": "Labour shortages",
        "Crime and illicit economic activity": "Illicit economic activity",
        "Decline in health and well-being": "Decline in health",
        "Chronic health conditions": "Chronic health conditions",
        "Illicit economic activity": "Illicit economic activity",
        "Prolonged economic downturn": "Economic downturn",
        "Asset bubble bursts": "Asset bubbles",
        "Employment crises": "Employment crises",
        "Debt crises": "Debt crises",
        "Debt": "Debt",
        "Intrastate violence": "Intrastate violence",
        "Online harms": "Online harms",
    }
    return shorts.get(name, name[:max_len])


def create_static_bump_chart(years, rankings_by_year, title, subtitle, filename,
                              max_rank=10, figsize=(18, 10)):
    """Create a static bump chart showing risk rankings over time."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Collect all risks that appear in any year
    all_risks = set()
    for year in years:
        if year in rankings_by_year:
            for r in rankings_by_year[year]:
                all_risks.add(r)
    
    # For each risk, build its trajectory
    for risk in all_risks:
        positions = {}
        for year in years:
            if year in rankings_by_year:
                risks = rankings_by_year[year]
                if risk in risks:
                    positions[year] = risks.index(risk) + 1
        
        if not positions:
            continue
        
        sorted_years = sorted(positions.keys())
        x_vals = sorted_years
        y_vals = [positions[y] for y in sorted_years]
        
        color = get_color(risk)
        short_name = shorten_name(risk)
        
        # Draw line
        ax.plot(x_vals, y_vals, '-o', color=color, linewidth=2.5, 
                markersize=8, markeredgecolor='white', markeredgewidth=1.5,
                zorder=3, alpha=0.85)
        
        # Label at last appearance
        last_year = sorted_years[-1]
        last_rank = positions[last_year]
        ax.annotate(short_name, (last_year, last_rank),
                   xytext=(8, 0), textcoords='offset points',
                   fontsize=8, va='center', color=color, fontweight='bold')
        
        # Label at first appearance
        first_year = sorted_years[0]
        first_rank = positions[first_year]
        ax.annotate(short_name, (first_year, first_rank),
                   xytext=(-8, 0), textcoords='offset points',
                   fontsize=8, va='center', ha='right', color=color, fontweight='bold')
    
    # Formatting
    ax.set_xlim(min(years) - 1.5, max(years) + 4)
    ax.set_ylim(max_rank + 0.5, 0.5)
    ax.set_yticks(range(1, max_rank + 1))
    ax.set_yticklabels([f"#{i}" for i in range(1, max_rank + 1)], fontsize=11)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=10, rotation=45, ha='right')
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, 
            fontsize=10, ha='center', va='bottom', style='italic', color='#666666')
    
    # Grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.grid(axis='x', alpha=0.15, linestyle='-')
    ax.set_axisbelow(True)
    
    # Legend
    legend_handles = [mpatches.Patch(color=c, label=cat) 
                     for cat, c in CATEGORY_COLORS.items()]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=9,
             framealpha=0.9, edgecolor='#cccccc')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved {filename}")


def create_animated_bump_chart(years, rankings_by_year, title, subtitle_template, 
                                filename, max_rank=10, figsize=(18, 10)):
    """Create an animated bump chart that reveals one year at a time."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Collect all risks
    all_risks = set()
    for year in years:
        if year in rankings_by_year:
            for r in rankings_by_year[year]:
                all_risks.add(r)
    
    def animate(frame_idx):
        ax.clear()
        
        # Show years up to current frame
        visible_years = years[:frame_idx + 1]
        current_year = visible_years[-1]
        
        for risk in all_risks:
            positions = {}
            for year in visible_years:
                if year in rankings_by_year:
                    risks = rankings_by_year[year]
                    if risk in risks:
                        positions[year] = risks.index(risk) + 1
            
            if not positions:
                continue
            
            sorted_yrs = sorted(positions.keys())
            x_vals = sorted_yrs
            y_vals = [positions[y] for y in sorted_yrs]
            
            color = get_color(risk)
            short_name = shorten_name(risk)
            
            # Draw line
            ax.plot(x_vals, y_vals, '-o', color=color, linewidth=2.5,
                    markersize=8, markeredgecolor='white', markeredgewidth=1.5,
                    zorder=3, alpha=0.85)
            
            # Label at last visible position
            last_year = sorted_yrs[-1]
            last_rank = positions[last_year]
            ax.annotate(short_name, (last_year, last_rank),
                       xytext=(8, 0), textcoords='offset points',
                       fontsize=8, va='center', color=color, fontweight='bold')
            
            # Label at first position
            first_year = sorted_yrs[0]
            first_rank = positions[first_year]
            if first_year != last_year:
                ax.annotate(short_name, (first_year, first_rank),
                           xytext=(-8, 0), textcoords='offset points',
                           fontsize=8, va='center', ha='right', color=color, fontweight='bold')
        
        # Formatting
        ax.set_xlim(min(years) - 1.5, max(years) + 4)
        ax.set_ylim(max_rank + 0.5, 0.5)
        ax.set_yticks(range(1, max_rank + 1))
        ax.set_yticklabels([f"#{i}" for i in range(1, max_rank + 1)], fontsize=11)
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) for y in years], fontsize=10, rotation=45, ha='right')
        
        # Grey out future years
        for i, yt in enumerate(ax.xaxis.get_ticklabels()):
            if years[i] > current_year:
                yt.set_alpha(0.2)
        
        subtitle = subtitle_template.format(year=current_year)
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes,
                fontsize=10, ha='center', va='bottom', style='italic', color='#666666')
        
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.grid(axis='x', alpha=0.15, linestyle='-')
        ax.set_axisbelow(True)
        
        legend_handles = [mpatches.Patch(color=c, label=cat)
                         for cat, c in CATEGORY_COLORS.items()]
        ax.legend(handles=legend_handles, loc='lower right', fontsize=9,
                 framealpha=0.9, edgecolor='#cccccc')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Create animation
    anim = animation.FuncAnimation(fig, animate, frames=len(years),
                                    interval=1200, repeat=True, repeat_delay=3000)
    
    # Save as GIF
    anim.save(OUTPUT_DIR / filename, writer='pillow', fps=1, dpi=120)
    plt.close()
    print(f"Saved {filename}")


def create_methodology_aware_charts():
    """Create charts that handle the methodology transition properly."""
    
    # =========================================================================
    # CHART 1: Short-term / Likelihood rankings (2007-2026)
    # =========================================================================
    # Era 1: Likelihood (2007-2021), top 5 then top 10
    # Era 3: Short-term 2-year severity (2023-2026)
    # Note discontinuity at 2022
    
    # For the animated chart, use top 5 for 2007-2017, top 10 for 2018+
    short_term_years_5 = list(range(2007, 2018))
    short_term_years_10 = list(range(2018, 2022)) + list(range(2023, 2027))
    
    # Build combined rankings dict
    short_term_rankings = {}
    for y in range(2007, 2022):
        short_term_rankings[y] = TOP_LIKELIHOOD[y]
    for y in range(2023, 2027):
        short_term_rankings[y] = TOP_SHORT_TERM[y]
    
    # Static chart: Top 5 era (2007-2017)
    create_static_bump_chart(
        years=list(range(2007, 2018)),
        rankings_by_year={y: TOP_LIKELIHOOD[y][:5] for y in range(2007, 2018)},
        title="WEF Global Risks: Top 5 by Likelihood (2007-2017)",
        subtitle="Source: WEF Global Risks Perception Survey | Risks ranked by perceived likelihood over next 10 years",
        filename="likelihood_top5_2007_2017.png",
        max_rank=5,
        figsize=(16, 8),
    )
    
    # Static chart: Top 10 Likelihood/Short-term (2018-2026)
    years_10 = list(range(2018, 2022)) + list(range(2023, 2027))
    rankings_10 = {}
    for y in range(2018, 2022):
        rankings_10[y] = TOP_LIKELIHOOD[y][:10]
    for y in range(2023, 2027):
        rankings_10[y] = TOP_SHORT_TERM[y][:10]
    
    create_static_bump_chart(
        years=years_10,
        rankings_by_year=rankings_10,
        title="WEF Global Risks: Short-Term Rankings (2018-2026)",
        subtitle="2018-2021: Top 10 by Likelihood | 2022: methodology transition (no data) | 2023-2026: Top 10 by 2-year Severity",
        filename="short_term_top10_2018_2026.png",
        max_rank=10,
        figsize=(18, 12),
    )
    
    # Animated version of short-term
    create_animated_bump_chart(
        years=years_10,
        rankings_by_year=rankings_10,
        title="WEF Global Risks: Short-Term Rankings (2018-2026)",
        subtitle_template="Showing data through {year} | 2018-2021: Likelihood | 2023-2026: 2-year Severity",
        filename="short_term_animated.gif",
        max_rank=10,
        figsize=(18, 12),
    )
    
    # =========================================================================
    # CHART 2: Long-term / Impact rankings (2007-2026)
    # =========================================================================
    
    # Static chart: Top 5 Impact (2007-2017)
    create_static_bump_chart(
        years=list(range(2007, 2018)),
        rankings_by_year={y: TOP_IMPACT[y][:5] for y in range(2007, 2018)},
        title="WEF Global Risks: Top 5 by Impact (2007-2017)",
        subtitle="Source: WEF Global Risks Perception Survey | Risks ranked by perceived impact if they occur",
        filename="impact_top5_2007_2017.png",
        max_rank=5,
        figsize=(16, 8),
    )
    
    # Top 10 Impact/Long-term (2018-2026)
    years_lt = list(range(2018, 2027))
    rankings_lt = {}
    for y in range(2018, 2022):
        rankings_lt[y] = TOP_IMPACT[y][:10]
    rankings_lt[2022] = SEVERITY_10Y_2022
    for y in range(2023, 2027):
        rankings_lt[y] = TOP_LONG_TERM[y][:10]
    
    create_static_bump_chart(
        years=years_lt,
        rankings_by_year=rankings_lt,
        title="WEF Global Risks: Long-Term Rankings (2018-2026)",
        subtitle="2018-2021: Top 10 by Impact | 2022: 10-year Severity (transitional) | 2023-2026: Top 10 by 10-year Severity",
        filename="long_term_top10_2018_2026.png",
        max_rank=10,
        figsize=(18, 12),
    )
    
    # Animated version
    create_animated_bump_chart(
        years=years_lt,
        rankings_by_year=rankings_lt,
        title="WEF Global Risks: Long-Term Rankings (2018-2026)",
        subtitle_template="Showing data through {year} | 2018-2021: Impact | 2022+: 10-year Severity",
        filename="long_term_animated.gif",
        max_rank=10,
        figsize=(18, 12),
    )
    
    # =========================================================================
    # CHART 3: Did long-term risks materialize as short-term risks?
    # =========================================================================
    create_materialization_chart()


def create_materialization_chart():
    """
    Analyze whether risks flagged as long-term concerns later appeared
    as short-term concerns.
    """
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Compare: risks in Impact/Long-term top 10 at time T
    # vs. risks in Likelihood/Short-term top 10 at time T+N
    
    # Use normalized names for comparison
    def norm(name):
        return NORMALIZE.get(name, name)
    
    # Build normalized long-term top 10 by year (always top 10 for prediction tracking)
    lt_by_year = {}
    for y in range(2018, 2022):
        lt_by_year[y] = [norm(r) for r in TOP_IMPACT[y][:10]]
    lt_by_year[2022] = [norm(r) for r in SEVERITY_10Y_2022]
    for y in range(2023, 2027):
        lt_by_year[y] = [norm(r) for r in TOP_LONG_TERM[y][:10]]
    
    # Build normalized short-term list by year (use top 10 for consistency)
    st_by_year = {}
    for y in range(2018, 2022):
        st_by_year[y] = [norm(r) for r in TOP_LIKELIHOOD[y][:10]]
    for y in range(2023, 2027):
        st_by_year[y] = [norm(r) for r in TOP_SHORT_TERM[y][:10]]
    
    # For each year's long-term list, check if those risks appeared in 
    # the short-term list within the next 2-5 years
    years = sorted(lt_by_year.keys())
    
    materialized_data = []
    for y in years:
        lt_risks = set(lt_by_year[y])
        future_st_risks = set()
        future_years_available = 0
        for future_y in range(y + 1, min(y + 6, 2027)):
            if future_y in st_by_year:
                future_st_risks.update(st_by_year[future_y])
                future_years_available += 1
        
        # Skip years with no future data to compare against
        if future_years_available == 0:
            continue
        
        overlap = lt_risks & future_st_risks
        materialized_data.append({
            'year': y,
            'total_lt': len(lt_risks),
            'materialized': len(overlap),
            'overlap_names': overlap,
            'not_materialized': lt_risks - future_st_risks,
            'future_years': future_years_available,
        })
    
    # Bar chart
    bar_years = [d['year'] for d in materialized_data]
    materialized_counts = [d['materialized'] for d in materialized_data]
    not_materialized = [d['total_lt'] - d['materialized'] for d in materialized_data]
    
    x = np.arange(len(bar_years))
    width = 0.6
    
    bars1 = ax.bar(x, materialized_counts, width, label='Appeared in short-term within 5 years',
                   color='#E91E63', alpha=0.8)
    bars2 = ax.bar(x, not_materialized, width, bottom=materialized_counts, 
                   label='Did not appear in short-term within 5 years',
                   color='#9E9E9E', alpha=0.5)
    
    ax.set_xlabel('Year of Long-Term Prediction', fontsize=12)
    ax.set_ylabel('Number of Risks (out of 10)', fontsize=12)
    ax.set_title('Did Long-Term Risk Predictions Materialize as Short-Term Concerns?', 
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(bar_years, fontsize=10)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 12)
    
    # Add count labels
    for i, (m, nm) in enumerate(zip(materialized_counts, not_materialized)):
        ax.text(i, m / 2, str(m), ha='center', va='center', fontweight='bold', color='white', fontsize=11)
        ax.text(i, m + nm / 2, str(nm), ha='center', va='center', fontweight='bold', color='#666', fontsize=11)
    
    # Add annotation about methodology change
    # Find index of 2022 in bar_years
    if 2022 in bar_years:
        idx_2022 = list(bar_years).index(2022)
        ax.axvline(x=idx_2022 - 0.5, color='red', linestyle='--', alpha=0.5)
        ax.text(idx_2022 - 0.4, 11, 'Methodology\nchange', fontsize=8, color='red', alpha=0.7)
    
    # Add note about future years lookback
    ax.text(0.5, -0.12, 
           "Note: Checks whether long-term top-10 risks later appeared in the short-term top-10 within 5 years.\n"
           "2026 excluded (no future data). Earlier years with fewer future data points may undercount.",
           transform=ax.transAxes, fontsize=8, ha='center', color='#888888', style='italic')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "materialization_analysis.png", dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()
    
    # Also print detailed analysis
    print("\n=== Materialization Analysis ===")
    for d in materialized_data:
        pct = d['materialized'] / d['total_lt'] * 100
        print(f"\n{d['year']} long-term predictions → short-term within 5 years:")
        print(f"  {d['materialized']}/{d['total_lt']} ({pct:.0f}%) materialized")
        if d['overlap_names']:
            print(f"  Materialized: {', '.join(sorted(d['overlap_names']))}")
        if d['not_materialized']:
            print(f"  Not yet: {', '.join(sorted(d['not_materialized']))}")
    
    print("\nSaved materialization_analysis.png")


def create_dual_panel_chart():
    """Create a side-by-side chart showing all short-term and long-term risks for 2026."""
    year = 2026
    short_risks = TOP_SHORT_TERM[year]
    long_risks = TOP_LONG_TERM[year]
    max_rank = max(len(short_risks), len(long_risks))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, max_rank * 0.4 + 2), sharey=True)
    
    for ax, risks, title in [(ax1, short_risks, f"Short Term (2 years)"),
                              (ax2, long_risks, f"Long Term (10 years)")]:
        for rank, risk in enumerate(risks, 1):
            color = get_color(risk)
            short_name = shorten_name(risk)
            
            ax.barh(rank, 0.8, color=color, alpha=0.85, height=0.7)
            ax.text(0.05, rank, f"{rank}. {short_name}", va='center', fontsize=8.5,
                   fontweight='bold', color='white')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(max_rank + 0.5, 0.5)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Add a faint line at rank 10 to delineate top 10
        ax.axhline(y=10.5, color='white', linewidth=1, alpha=0.5, linestyle='--')
    
    fig.suptitle(f"WEF Global Risks Report {year}: All {max_rank} Risks Ranked by Severity", 
                fontsize=16, fontweight='bold', y=0.99)
    
    # Legend
    legend_handles = [mpatches.Patch(color=c, label=cat)
                     for cat, c in CATEGORY_COLORS.items()]
    fig.legend(handles=legend_handles, loc='lower center', ncol=5, fontsize=10,
              framealpha=0.9, edgecolor='#cccccc', bbox_to_anchor=(0.5, 0.005))
    
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.savefig(OUTPUT_DIR / "dual_panel_2026.png", dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()
    print("Saved dual_panel_2026.png")


def create_full_ranking_bump_chart(ranking_type="short"):
    """Create a bump chart showing ALL risks (not just top 10) across 2023-2026.
    
    Args:
        ranking_type: "short" for 2-year severity, "long" for 10-year severity
    """
    data = TOP_SHORT_TERM if ranking_type == "short" else TOP_LONG_TERM
    years = sorted(data.keys())
    
    # Use normalized names for tracking
    def norm(name):
        return NORMALIZE.get(name, name)
    
    # Collect all normalized risk names across all years
    all_norms = set()
    for year in years:
        for risk in data[year]:
            all_norms.add(norm(risk))
    
    # Build positions for each normalized risk
    risk_positions = {}  # norm_name -> {year: (rank, raw_name)}
    for year in years:
        for rank, risk in enumerate(data[year], 1):
            n = norm(risk)
            if n not in risk_positions:
                risk_positions[n] = {}
            risk_positions[n][year] = (rank, risk)
    
    max_rank = max(len(data[y]) for y in years)
    
    if ranking_type == "short":
        title = "WEF Global Risks: All Risks by 2-Year Severity (2023-2026)"
        subtitle = "Full ranking of all surveyed risks | Source: Global Risks Perception Survey"
        fname = "full_ranking_short_term.png"
    else:
        title = "WEF Global Risks: All Risks by 10-Year Severity (2023-2026)"
        subtitle = "Full ranking of all surveyed risks | Source: Global Risks Perception Survey"
        fname = "full_ranking_long_term.png"
    
    fig, ax = plt.subplots(figsize=(16, max_rank * 0.45 + 3))
    
    for norm_name, positions in risk_positions.items():
        sorted_yrs = sorted(positions.keys())
        x_vals = sorted_yrs
        y_vals = [positions[y][0] for y in sorted_yrs]
        
        latest_risk = positions[sorted_yrs[-1]][1]
        color = get_color(latest_risk)
        short_name = shorten_name(latest_risk)
        
        # Draw line
        ax.plot(x_vals, y_vals, '-o', color=color, linewidth=1.8,
                markersize=6, markeredgecolor='white', markeredgewidth=0.8,
                zorder=3, alpha=0.75)
        
        # Label at last year
        last_year = sorted_yrs[-1]
        last_rank = positions[last_year][0]
        ax.annotate(short_name, (last_year, last_rank),
                   xytext=(8, 0), textcoords='offset points',
                   fontsize=6.5, va='center', color=color, fontweight='bold')
        
        # Label at first year
        first_year = sorted_yrs[0]
        first_rank = positions[first_year][0]
        if len(sorted_yrs) > 1:
            ax.annotate(short_name, (first_year, first_rank),
                       xytext=(-8, 0), textcoords='offset points',
                       fontsize=6.5, va='center', ha='right', color=color, fontweight='bold')
    
    # Add top 10 demarcation
    ax.axhline(y=10.5, color='red', linewidth=0.8, alpha=0.4, linestyle='--')
    ax.text(years[0] - 0.3, 10.5, 'Top 10', fontsize=7, color='red', alpha=0.6,
           ha='right', va='center')
    
    ax.set_xlim(min(years) - 2.5, max(years) + 5)
    ax.set_ylim(max_rank + 0.5, 0.5)
    ax.set_yticks(range(1, max_rank + 1))
    ax.set_yticklabels([f"#{i}" for i in range(1, max_rank + 1)], fontsize=8)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=11)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.text(0.5, 1.01, subtitle, transform=ax.transAxes,
            fontsize=9, ha='center', va='bottom', style='italic', color='#666666')
    
    ax.grid(axis='y', alpha=0.15, linestyle='-')
    ax.grid(axis='x', alpha=0.1, linestyle='-')
    ax.set_axisbelow(True)
    
    legend_handles = [mpatches.Patch(color=c, label=cat)
                     for cat, c in CATEGORY_COLORS.items()]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=9,
             framealpha=0.9, edgecolor='#cccccc')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved {fname}")


def create_full_timeline_chart(ranking_type="short"):
    """Create a comprehensive bump chart spanning the full 2007-2026 timeline.
    
    Args:
        ranking_type: "short" for likelihood/short-term, "long" for impact/long-term
    """
    if ranking_type == "short":
        years = list(range(2007, 2022)) + list(range(2023, 2027))
        rankings = {}
        for y in range(2007, 2022):
            rankings[y] = TOP_LIKELIHOOD[y]
        for y in range(2023, 2027):
            rankings[y] = TOP_SHORT_TERM[y][:10]
        title = "WEF Global Risks: Short-Term Risk Rankings (2007-2026)"
        subtitle = ("Top 5 by Likelihood (2007-2017) → Top 10 by Likelihood (2018-2021) "
                   "→ Top 10 by 2-year Severity (2023-2026)\n"
                   "⚠ Methodology changed in 2022: Likelihood → Severity. 2022 has no short-term data.")
        fname = "full_timeline_short_term.png"
        max_rank = 10
    else:
        years = list(range(2007, 2027))
        rankings = {}
        for y in range(2007, 2022):
            rankings[y] = TOP_IMPACT[y]
        rankings[2022] = SEVERITY_10Y_2022
        for y in range(2023, 2027):
            rankings[y] = TOP_LONG_TERM[y][:10]
        title = "WEF Global Risks: Long-Term Risk Rankings (2007-2026)"
        subtitle = ("Top 5 by Impact (2007-2017) → Top 10 by Impact (2018-2021) "
                   "→ Top 10 by 10-year Severity (2022-2026)\n"
                   "⚠ Methodology changed in 2022: Impact → Severity.")
        fname = "full_timeline_long_term.png"
        max_rank = 10
    
    fig, ax = plt.subplots(figsize=(24, 14))
    
    # Collect all risks
    all_risks = set()
    for y in years:
        if y in rankings:
            for r in rankings[y]:
                all_risks.add(r)
    
    # Normalize names for tracking across years
    def norm(name):
        return NORMALIZE.get(name, name)
    
    # Group risks by normalized name
    norm_groups = {}
    for risk in all_risks:
        n = norm(risk)
        if n not in norm_groups:
            norm_groups[n] = []
        norm_groups[n].append(risk)
    
    # Draw trajectories for each normalized risk
    for norm_name, raw_names in norm_groups.items():
        positions = {}
        for year in years:
            if year in rankings:
                for rank_idx, risk in enumerate(rankings[year]):
                    if norm(risk) == norm_name:
                        positions[year] = (rank_idx + 1, risk)
                        break
        
        if not positions:
            continue
        
        sorted_yrs = sorted(positions.keys())
        x_vals = sorted_yrs
        y_vals = [positions[y][0] for y in sorted_yrs]
        
        # Use color from most recent appearance
        latest_risk = positions[sorted_yrs[-1]][1]
        color = get_color(latest_risk)
        short_name = shorten_name(latest_risk)
        
        # Draw connecting line segments (skip gaps > 1 year)
        for i in range(len(sorted_yrs) - 1):
            y1, y2 = sorted_yrs[i], sorted_yrs[i + 1]
            # Allow gaps for methodology change
            if y2 - y1 <= 2:
                ax.plot([y1, y2], [positions[y1][0], positions[y2][0]], '-',
                       color=color, linewidth=2, alpha=0.7, zorder=2)
            else:
                # Draw dashed line for large gaps
                ax.plot([y1, y2], [positions[y1][0], positions[y2][0]], '--',
                       color=color, linewidth=1.5, alpha=0.4, zorder=2)
        
        # Draw points
        ax.scatter(x_vals, y_vals, s=60, c=color, zorder=3, 
                  edgecolors='white', linewidths=1)
        
        # Label at last appearance (right side)
        last_year = sorted_yrs[-1]
        last_rank = positions[last_year][0]
        ax.annotate(short_name, (last_year, last_rank),
                   xytext=(10, 0), textcoords='offset points',
                   fontsize=7.5, va='center', color=color, fontweight='bold')
    
    # Add methodology change indicator
    if ranking_type == "short":
        ax.axvline(x=2021.5, color='red', linestyle='--', alpha=0.4, linewidth=1.5)
        ax.text(2021.5, 0.5, '← Likelihood | Severity →', fontsize=8, 
               color='red', alpha=0.6, ha='center', va='bottom',
               transform=ax.get_xaxis_transform())
    else:
        ax.axvline(x=2021.5, color='red', linestyle='--', alpha=0.4, linewidth=1.5)
        ax.text(2021.5, 0.5, '← Impact | Severity →', fontsize=8,
               color='red', alpha=0.6, ha='center', va='bottom',
               transform=ax.get_xaxis_transform())
    
    # Also mark the top-5 to top-10 expansion
    ax.axvline(x=2017.5, color='blue', linestyle=':', alpha=0.3, linewidth=1)
    ax.text(2017.5, 0.5, 'Top 5 → Top 10', fontsize=7, color='blue', alpha=0.5,
           ha='center', va='bottom', transform=ax.get_xaxis_transform())
    
    # Formatting
    ax.set_xlim(min(years) - 1, max(years) + 4.5)
    ax.set_ylim(max_rank + 0.5, 0.5)
    ax.set_yticks(range(1, max_rank + 1))
    ax.set_yticklabels([f"#{i}" for i in range(1, max_rank + 1)], fontsize=11)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=9, rotation=45, ha='right')
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
    ax.text(0.5, 1.015, subtitle, transform=ax.transAxes,
            fontsize=9, ha='center', va='bottom', style='italic', color='#666666')
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.grid(axis='x', alpha=0.1, linestyle='-')
    ax.set_axisbelow(True)
    
    legend_handles = [mpatches.Patch(color=c, label=cat)
                     for cat, c in CATEGORY_COLORS.items()]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=10,
             framealpha=0.9, edgecolor='#cccccc')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved {fname}")


if __name__ == "__main__":
    print("Creating WEF Global Risk Report visualizations...")
    print("=" * 60)
    
    # 1. Full timeline charts (top 10 across all years)
    print("\n1. Creating full timeline charts...")
    create_full_timeline_chart("short")
    create_full_timeline_chart("long")
    
    # 2. Top 5 era charts (2007-2017) + methodology-aware charts
    print("\n2. Creating Top 5 era charts (2007-2017)...")
    create_methodology_aware_charts()
    
    # 3. Dual panel for 2026 (all ranks)
    print("\n3. Creating dual panel chart for 2026...")
    create_dual_panel_chart()
    
    # 4. Full ranking bump charts (all 32-34 risks, 2023-2026)
    print("\n4. Creating full ranking bump charts (all risks)...")
    create_full_ranking_bump_chart("short")
    create_full_ranking_bump_chart("long")
    
    print("\n" + "=" * 60)
    print("All visualizations saved to output/")
