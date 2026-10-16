def choose(baseline,candidate,before,after):
    """A reduction in one metric cannot compensate for an increase in another."""
    return candidate if all(a<=b for a,b in zip(after.values,before.values)) and after!=before else baseline
