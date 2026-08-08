"""
Nestle DOM planner dashboard.

A small Streamlit app that walks through the planner workflow: what the data
looks like, what each method achieved, and which orders we recommend moving.

Everything shown is fixed. The numbers live in results.py and were produced by
the notebooks, so the app opens instantly and needs no data files.

Run it with:
    streamlit run app.py
"""
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import results as R

st.set_page_config(page_title="Nestle DOM Planner", page_icon="\U0001F4E6", layout="wide")

NAVY, ORANGE, GREEN, TEAL, RED = "#1f3864", "#c55a11", "#548235", "#2e75b6", "#833c0c"
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "Figures")


def fig_path(name):
    p = os.path.join(FIGDIR, name)
    return p if os.path.isfile(p) else None


def money(v):
    return f"${v:,.0f}"


# ---------------------------------------------------------------- sidebar
st.sidebar.title("Nestle DOM")
st.sidebar.caption("Distributed Order Management")
PAGE = st.sidebar.radio("Page", [
    "Dataset overview",
    "Method comparison",
    "Planner view",
    "Fill rate and objective",
    "Runtime",
    "Order and DC flow",
])
st.sidebar.divider()
st.sidebar.caption(
    f"{R.DATASET['orders']:,} orders  ·  {R.DATASET['skus']:,} SKUs  ·  "
    f"{R.DATASET['dcs']} DCs\n\n{R.DATASET['window']}")
st.sidebar.caption("All figures are fixed results from the notebooks.")


# ================================================================ 1. dataset
if PAGE == "Dataset overview":
    st.title("Dataset overview")
    st.write("What is in the data, and which orders need a decision.")

    c = st.columns(4)
    c[0].metric("Open orders", f"{R.DATASET['orders']:,}")
    c[1].metric("SKUs", f"{R.DATASET['skus']:,}")
    c[2].metric("Distribution centres", R.DATASET["dcs"])
    c[3].metric("Orders needing a decision", R.DATASET["focus"])

    st.divider()
    st.subheader("The order funnel")
    st.write(
        f"An order needs a decision for one of two reasons. Either it is **short of stock** at its "
        f"own DC ({R.DATASET['short_of_stock']} orders), or it ships on a day when that DC has "
        f"**no dock slot left** ({R.DATASET['no_dock']} orders). "
        f"That gives **{R.DATASET['focus']} focus orders**. The other "
        f"{R.DATASET['untouched']} are fine and stay where they are.")

    funnel = pd.DataFrame({
        "stage": ["Open orders", "Short of stock", "+ no dock that day",
                  "= Focus orders", "Fine, stay put"],
        "orders": [R.DATASET["orders"], R.DATASET["short_of_stock"], R.DATASET["no_dock"],
                   R.DATASET["focus"], R.DATASET["untouched"]],
    })
    fig = px.bar(funnel, x="orders", y="stage", orientation="h", text="orders",
                 color="stage",
                 color_discrete_sequence=[NAVY, ORANGE, TEAL, RED, GREEN])
    fig.update_layout(showlegend=False, height=300, yaxis_title="", xaxis_title="orders",
                      yaxis={"categoryorder": "array",
                             "categoryarray": funnel["stage"][::-1]})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("The files")
    st.dataframe(R.FILES, use_container_width=True, hide_index=True)

    st.subheader("Distribution centres")
    st.write("Eight DCs serve the network: " + ", ".join(str(d) for d in R.DC_LIST) + ".")

    with st.expander("What the data does not contain"):
        st.dataframe(R.ASSUMPTIONS, use_container_width=True, hide_index=True)


# ================================================================ 2. comparison
elif PAGE == "Method comparison":
    st.title("Baseline, greedy and quantum")
    st.write("Every classical method is measured on the same 472 orders, "
             "with the same objective and the same rule checks.")

    st.subheader("Classical methods")
    show = R.CLASSICAL.copy()
    show["objective"] = show["objective"].map(money)
    show["penalty"] = show["penalty"].map(money)
    show["freight"] = show["freight"].map(money)
    show["fill"] = R.CLASSICAL["fill"].map(lambda v: f"{v:.2f}%")
    show["runtime"] = R.CLASSICAL["runtime"].map(lambda v: f"{v:.2f}s")
    st.dataframe(show.drop(columns=["short"]), use_container_width=True, hide_index=True)

    gain = R.OPT_OBJ - R.BASE_OBJ
    c = st.columns(4)
    c[0].metric("Best objective", money(R.OPT_OBJ), f"+{money(gain)} over doing nothing")
    c[1].metric("Fill rate", "93.28%", "+2.81 points")
    c[2].metric("Orders moved", "66")
    c[3].metric("Greedy gap", "3.21%", "below the best answer", delta_color="inverse")

    st.info(
        "**The surprise.** The exact solver moves 66 orders against the greedy's 41, and still "
        "pays $15,285 **less** in extra freight. Planning every order together lets it pick "
        "cheaper lanes and connect moves: emptying one DC frees stock that lets another order "
        "move in.")

    st.divider()
    st.subheader("How far the greedy is from the best answer")
    st.write("The percentage gap looks small because most of the money sits in orders that were "
             "never in trouble. The more useful measure is the share of the gain that can "
             "actually be reached.")
    reach = pd.DataFrame([
        dict(method="Leave everything alone", objective=R.BASE_OBJ, share_of_reachable_gain=0.0),
        dict(method="Greedy 2A", objective=R.GREEDY_OBJ,
             share_of_reachable_gain=(R.GREEDY_OBJ - R.BASE_OBJ) / gain * 100),
        dict(method="Exact MILP", objective=R.OPT_OBJ, share_of_reachable_gain=100.0),
    ])
    fig = px.bar(reach, x="method", y="share_of_reachable_gain", text_auto=".1f",
                 color="method", color_discrete_sequence=[NAVY, TEAL, RED])
    fig.update_layout(showlegend=False, height=300,
                      yaxis_title="share of reachable gain (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Quantum")
    st.write("Three separate pieces of work, so they are shown separately rather than merged.")

    t1, t2, t3 = st.tabs(["Checked against every answer", "The batched run", "Hybrid"])

    with t1:
        st.write("3 orders and 3 DCs is 9 variables and only 27 valid combinations, so we listed "
                 "all of them. This checks the encoding is right before scaling it up.")
        q = R.QUANTUM_SMALL.copy()
        q["objective"] = q["objective"].map(lambda v: f"{v:,.1f}")
        q["fill"] = R.QUANTUM_SMALL["fill"].map(lambda v: f"{v:.2f}%")
        st.dataframe(q, use_container_width=True, hide_index=True)
        st.success("Ranking the 27 valid answers by QUBO energy gives the same order as ranking "
                   "them by money. So the encoding is faithful, not just lucky.")
        fig = px.line(R.QAOA_RUNS, x="run", y="objective", markers=True,
                      title="QAOA is stable across runs")
        fig.add_hline(y=760_517.9, line_dash="dash", line_color=GREEN,
                      annotation_text="true best")
        fig.update_traces(line_color=RED)
        fig.update_layout(height=300, yaxis_title="objective ($)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Mean $760,341 across 5 runs, spread 0.046%. Four of five were exactly best, "
                   "and all five beat leaving everything alone. No repair was needed.")

    with t2:
        n = R.QUBIT_NOTE
        c = st.columns(4)
        c[0].metric("Qubits per batch", n["qubits_per_batch"])
        c[1].metric("Slack qubits", n["slack_qubits"])
        c[2].metric("Batches", n["batches"])
        c[3].metric("Total solve time", f"{n['total_solve_s']}s")
        q = R.QUANTUM_BATCHED.copy()
        q["objective"] = q["objective"].map(money)
        q["fill"] = R.QUANTUM_BATCHED["fill"].map(lambda v: f"{v:.2f}%")
        st.dataframe(q, use_container_width=True, hide_index=True)

        b = R.BATCHES
        fig = go.Figure()
        fig.add_bar(x=b["batch"], y=b["default"], name="leave alone", marker_color=NAVY)
        fig.add_bar(x=b["batch"], y=b["quantum"], name="quantum", marker_color=RED)
        fig.update_layout(barmode="group", height=320, xaxis_title="batch",
                          yaxis_title="objective ($)", title="Objective per batch")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Gain over doing nothing: {money(b['lift'].sum())} (+10.0%). "
                   "Quantum matched or beat the greedy on 15 of 15 batches, with no rule "
                   "violations.")

    with t3:
        st.write("A classical step proposes fulfilment options, and QAOA picks among them.")
        st.dataframe(R.HYBRID, use_container_width=True, hide_index=True)
        st.caption(f"Every batch closed with a gap of exactly zero, in "
                   f"{R.QUBIT_NOTE['hybrid_total_s']} seconds of quantum time in total.")

    st.warning(
        "**How to read the quantum result.** The quantum solver **matches** the greedy on the "
        "batched run: the difference is $0 on every batch. At 18 qubits a batch is small enough "
        "that both methods find the same best answer. This shows the encoding is **correct**, "
        "not that quantum is **faster**.")


# ================================================================ 3. planner
elif PAGE == "Planner view":
    st.title("Planner view")
    st.write("What we recommend, and what it is worth. No mathematics on this page.")

    st.success(
        "Of the **472** orders that cannot be filled completely where they sit, we recommend "
        "moving **66** to a different distribution centre. This fills **40,771** more cases, "
        "raises the fill rate from **90.5%** to **93.3%**, avoids **$52,416** of customer "
        "penalties, and costs **$57,401** in extra freight. Net gain: **$1,929,835**.")

    st.subheader("Leave everything, or apply the plan")
    st.dataframe(R.PLANNER_TOTALS, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Why an order moves")
    st.write("An order moves only when the receiving DC can fill it at least **5 percentage "
             "points** and **100 cases** better than where it sits now, and only when that gain "
             "is worth more than the extra freight. Orders that already fill well are left alone.")

    st.subheader("The largest recommendations")
    top = st.slider("How many to show", 3, len(R.TOP_MOVES), 10)
    t = R.TOP_MOVES.head(top).copy()
    view = pd.DataFrame({
        "Order": t["order"].astype(str),
        "From": t["from_dc"].astype(str),
        "To": t["to_dc"].astype(str),
        "Fill rate": t["fill_before"].astype(str) + "% \u2192 " + t["fill_after"].astype(str) + "%",
        "Extra cases": t["extra_cases"].map(lambda v: f"{v:,}"),
        "Penalty saved": t["penalty_saved"].map(lambda v: money(v) if v else "-"),
        "Extra freight": t["extra_freight"].map(money),
        "Net gain": t["net_gain"].map(money),
    })
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption("A negative freight figure means the move is cheaper to ship as well as fuller.")

    st.divider()
    st.subheader("Before releasing the plan")
    st.markdown(
        "- **Stock at the receiving DC is committed.** The plan assumes the free stock shown is "
        "still free. Re-run it if a large order has arrived since.\n"
        "- **No forecast reserve, no holiday calendar.** No stock is held back for the receiving "
        "DC's own upcoming orders, and ship dates avoid weekends but not holidays. Check moves "
        "into 5490 and 5410 most carefully.")


# ================================================================ 4. fill rate
elif PAGE == "Fill rate and objective":
    st.title("Fill rate and objective")
    st.write("What each method buys, and what it pays for it.")

    b = R.CLASSICAL.iloc[0]
    d = R.CLASSICAL.copy()
    d["gain"] = d["objective"] - b["objective"]
    d["extra_freight"] = d["freight"] - b["freight"]
    d["fill_gain"] = d["fill"] - b["fill"]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(d, x="short", y="gain", text_auto=".3s", color="short",
                     color_discrete_sequence=[NAVY, TEAL, TEAL, RED],
                     title="Objective gained over doing nothing")
        fig.update_layout(showlegend=False, height=330, xaxis_title="", yaxis_title="$")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(d, x="short", y="fill", text_auto=".2f", color="short",
                     color_discrete_sequence=[NAVY, TEAL, TEAL, RED],
                     title="Fill rate")
        fig.update_layout(showlegend=False, height=330, xaxis_title="", yaxis_title="%")
        fig.update_yaxes(range=[88, 95])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("What the gain costs")
    fig = go.Figure()
    fig.add_bar(x=d["short"], y=d["penalty"], name="penalty paid", marker_color=ORANGE)
    fig.add_bar(x=d["short"], y=d["extra_freight"], name="extra freight", marker_color=GREEN)
    fig.update_layout(barmode="group", height=330, yaxis_title="$", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Filling more cases means shipping from farther away. The objective decides "
               "whether that trade is worth making.")

    st.divider()
    st.subheader("Why most moves are not possible")
    rej = R.REJECTIONS.copy()
    rej["share"] = rej["count"] / rej["count"].sum() * 100
    fig = px.bar(rej, x="count", y="reason", orientation="h", text="count",
                 color_discrete_sequence=[GREEN])
    fig.update_layout(height=330, yaxis_title="", xaxis_title="candidate moves rejected",
                      yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.info("The blocks are business rules, not the warehouse. The 5% gate and missing SKU "
            "assortment cause 86% of rejections. Docks and picking together block 28 of 3,659.")

    st.divider()
    st.subheader("Where the two methods disagree")
    st.write("Same rules, same data, different searches.")
    fig = px.pie(R.DISAGREEMENT, values="orders", names="case", hole=0.45,
                 color_discrete_sequence=[RED, GREEN, TEAL, ORANGE])
    fig.update_layout(height=330)
    st.plotly_chart(fig, use_container_width=True)


# ================================================================ 5. runtime
elif PAGE == "Runtime":
    st.title("Runtime")
    st.write("How long each method takes, and how that grows with the problem.")

    fig = px.bar(R.RUNTIME, x="seconds", y="method", orientation="h", color="group",
                 text="seconds", log_x=True,
                 color_discrete_map={"classical": NAVY, "quantum": RED})
    fig.update_layout(height=380, yaxis_title="", xaxis_title="seconds (log scale)",
                      yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("A log scale is used because the range is four orders of magnitude. "
               "Quantum times are for smaller subsets, so they are not directly comparable "
               "with the 472-order classical runs.")

    st.divider()
    st.subheader("How the exact model grows")
    st.write("Five sizes of the same problem, each solved to the proven best answer.")
    st.dataframe(R.SCALING, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(R.SCALING, x="orders", y="wall_s", markers=True,
                      title="Solve time")
        fig.update_traces(line_color=RED)
        fig.update_layout(height=320, xaxis_title="focus orders", yaxis_title="seconds")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.line(R.SCALING, x="orders", y="gap_pct", markers=True,
                      title="How far the greedy falls behind")
        fig.update_traces(line_color=ORANGE)
        fig.update_layout(height=320, xaxis_title="focus orders",
                          yaxis_title="% below the best answer")
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**The trend that matters.** The greedy's gap grows from **0.84%** at 50 orders to "
        "**3.21%** at 472. On small problems a greedy is nearly as good as the best answer. "
        "The more orders compete for the same stock, the more it loses by never going back. "
        "A larger real order book would widen this further.")

    st.subheader("What grows")
    fig = go.Figure()
    fig.add_scatter(x=R.SCALING["orders"], y=R.SCALING["binaries"], mode="lines+markers",
                    name="binary variables", line_color=NAVY)
    fig.add_scatter(x=R.SCALING["orders"], y=R.SCALING["rows"] / 100, mode="lines+markers",
                    name="constraint rows / 100", line_color=TEAL)
    fig.update_layout(height=320, xaxis_title="focus orders", yaxis_title="count")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Binary variables are orders times candidate DCs. Constraint rows are mostly "
               "stock rows, which are DC times SKU times day.")


# ================================================================ 6. flow
elif PAGE == "Order and DC flow":
    st.title("Order and DC flow")
    st.write("Where the reassigned orders come from and where they go.")

    st.subheader("Which DCs receive the orders")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(R.DESTINATIONS, x="dc", y="orders_received", text="orders_received",
                     color_discrete_sequence=[TEAL], title="Orders received")
        fig.update_layout(height=330, xaxis_title="receiving DC", yaxis_title="orders",
                          xaxis_type="category")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(R.DESTINATIONS, x="dc", y="net_gain", text_auto=".3s",
                     color_discrete_sequence=[RED], title="Net gain")
        fig.update_layout(height=330, xaxis_title="receiving DC", yaxis_title="$",
                          xaxis_type="category")
        st.plotly_chart(fig, use_container_width=True)

    st.caption("DC 5490 receives the most orders (22) and brings the largest share of the "
               "gain ($208k).")

    st.divider()
    st.subheader("Flow of the largest moves")
    st.write("Each band is one order moving from its own DC to a new one. The width is the net "
             "gain. Only the ten largest moves are shown, because those are the ones with "
             "order-level detail.")

    moves = R.TOP_MOVES
    froms = sorted(moves["from_dc"].unique())
    tos = sorted(moves["to_dc"].unique())
    labels = [f"from {d}" for d in froms] + [f"to {d}" for d in tos]
    fidx = {d: i for i, d in enumerate(froms)}
    tidx = {d: i + len(froms) for i, d in enumerate(tos)}

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=18, thickness=16,
                  color=[NAVY] * len(froms) + [RED] * len(tos)),
        link=dict(source=[fidx[r.from_dc] for r in moves.itertuples()],
                  target=[tidx[r.to_dc] for r in moves.itertuples()],
                  value=[r.net_gain for r in moves.itertuples()],
                  label=[f"order {r.order}: {money(r.net_gain)}" for r in moves.itertuples()],
                  color="rgba(46,117,182,0.35)")))
    fig.update_layout(height=420, font_size=12)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Look at one order")
    pick = st.selectbox("Choose an order", moves["order"].astype(str).tolist())
    row = moves[moves["order"].astype(str) == pick].iloc[0]

    c = st.columns(4)
    c[0].metric("Moves from", str(row.from_dc), f"to {row.to_dc}")
    c[1].metric("Fill rate", f"{row.fill_after}%", f"+{row.fill_after - row.fill_before} points")
    c[2].metric("Extra cases", f"{row.extra_cases:,}")
    c[3].metric("Net gain", money(row.net_gain))

    detail = pd.DataFrame([
        dict(item="Penalty saved", value=money(row.penalty_saved) if row.penalty_saved else "-"),
        dict(item="Extra freight", value=money(row.extra_freight)),
        dict(item="Fill rate before", value=f"{row.fill_before}%"),
        dict(item="Fill rate after", value=f"{row.fill_after}%"),
    ])
    st.dataframe(detail, use_container_width=True, hide_index=True)

    if row.extra_freight < 0:
        st.success("This move is cheaper to ship as well as fuller.")

st.divider()
st.caption("Nestle DOM  ·  WISER Global Quantum+AI Program 2026  ·  "
           "All figures are fixed results from the notebooks.")
