"""Classification of complete, limited and failed outcomes."""

def classify(metrics,*,valid=True,opaque=False):
    if not valid:
        return 'falha'
    return 'sucesso' if metrics.clean and not opaque else 'limitações'
