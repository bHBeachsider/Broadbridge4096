"""Denominator-explicit, descriptive diagram metrics. Never training approval.

Wilson intervals assume independent Bernoulli trials. Edges within drawings and
variants of one family are correlated; these intervals alone cannot qualify a
deployment, and a replay of development data is never a held-out evaluation.
"""
from math import sqrt


def count(value):
    if type(value) is not int or value<0:raise ValueError('Counts must be nonnegative integers')
    return value


def proportion(successes,denominator):
    count(successes);count(denominator)
    if successes>denominator:raise ValueError('Successes exceed denominator')
    result=dict(successes=successes,denominator=denominator,estimate=None,lower_95=None,upper_95=None)
    if not denominator:return result
    z=1.959963984540054;p=successes/denominator;n=denominator
    scale=1+z*z/n;center=(p+z*z/(2*n))/scale
    half=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/scale
    result.update(estimate=p,lower_95=max(0,center-half),upper_95=min(1,center+half))
    return result


def summarize(*,tp,fp,fn,direction_claims,directions_correct,reference_directions,
              directions_reversed,unsupported_directions,evidence_violations,checker_rejections):
    values=locals().copy()
    for value in values.values():count(value)
    if directions_correct+directions_reversed+unsupported_directions>direction_claims:
        raise ValueError('Inconsistent direction counts')
    return {'counts':values,'edge_precision':proportion(tp,tp+fp),'edge_recall':proportion(tp,tp+fn),
            'direction_precision':proportion(directions_correct,direction_claims),
            'direction_recovery':proportion(directions_correct,reference_directions),
            # Categories can overlap. This sum is flags, not unique incidents.
            'critical_error_flags':directions_reversed+unsupported_directions+evidence_violations,
            'interval_method':'two-sided Wilson 95%; iid descriptive approximation',
            'training_approved':False}
