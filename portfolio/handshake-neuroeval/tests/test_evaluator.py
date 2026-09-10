from neuroeval import evaluate


def test_complete_answer_scores_higher():
    strong = evaluate("Action potentials propagate because voltage-gated sodium channels depolarize the membrane, followed by potassium-channel-mediated repolarization. Evidence from electrophysiology supports this mechanism, although channel kinetics can vary by neuron type.", ["sodium channels", "potassium", "repolarization"])
    weak = evaluate("Neurons definitely work because electricity happens.", ["sodium channels", "potassium", "repolarization"])
    assert strong.total > weak.total
    assert strong.factuality == 5
    assert weak.factuality == 0


def test_overconfidence_is_flagged():
    result = evaluate("This definitely proves the receptor always causes the behavior.")
    assert any("overconfident" in flag for flag in result.flags)
