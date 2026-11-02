"""Eval de memória separado do roteamento: `expect.expects_fact` + linha "memória" × "roteamento"."""
from evals import memory_metrics, run_evals


def row(id_, **checks):
    return {"id": id_, "split": "memory", "crash": None, "checks": checks}


def test_score_adds_memory_check_only_for_cases_that_declare_expects_fact():
    case = {"id": "m", "split": "memory", "message": "x",
            "expect": {"intent": "records", "expects_fact": ["TX1007", "R$ 75,00"]}}
    ok = run_evals.score(case, {"intent": "records", "answer": "A TX1007 foi de 75.0 reais."})
    bad = run_evals.score(case, {"intent": "records", "answer": "A TX1008 foi de 75.0 reais."})
    assert ok["memory"] is True and bad["memory"] is False
    legacy = {"id": "m", "split": "memory", "message": "x", "expect": {"intent": "records"}}
    assert "memory" not in run_evals.score(legacy, {"intent": "records", "answer": "ok"})


def test_loss_is_attributed_to_routing_or_to_memory():
    rows = [row("a", intent=True, tools=True, memory=True, numbers=True),
            row("b", intent=False, tools=True, memory=True, numbers=True),   # só roteamento
            row("c", intent=True, tools=True, memory=False, numbers=True),   # só memória (fato)
            row("d", intent=True, tools=True, numbers=False),                # só memória (número, sem expects_fact)
            row("e", intent=False, memory=False, numbers=True)]              # as duas
    s = memory_metrics.memory_vs_routing(rows)["memory"]
    assert (s["n"], s["routing_acc"], s["memory_acc"], s["pass_at_1"]) == (5, 60.0, 40.0, 20.0)
    assert s["facts_acc"] == 50.0 and s["facts_n"] == 4 and s["numbers_acc"] == 80.0
    assert s["only_routing_fails"] == ["b"] and s["only_memory_fails"] == ["c", "d"] and s["both_fail"] == ["e"]
    line = memory_metrics.lines({"memory": s})[0]
    assert "**memória** 40.0%" in line and "**roteamento** 60.0%" in line


def test_splits_without_memory_checks_are_left_out_and_crashes_do_not_count():
    other = {"id": "z", "split": "official", "crash": None, "checks": {"intent": True}}
    crashed = {**row("x", intent=False), "crash": "boom"}
    assert memory_metrics.memory_vs_routing([other, crashed]) == {}


def test_report_carries_the_memory_routing_line(tmp_path):
    report = run_evals.run(split="memory", out=tmp_path / "m.json")
    assert "memory_routing" in report and report["memory_routing"]["memory"]["n"] >= 1
    assert "Memória × roteamento" in run_evals.to_markdown(report)
