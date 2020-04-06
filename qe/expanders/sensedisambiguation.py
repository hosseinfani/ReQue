from pywsd import disambiguate

import sys
sys.path.extend(['../qe'])

from expanders.abstractqexpander import AbstractQExpander

class SenseDisambiguation(AbstractQExpander):
    def __init__(self, replace=False):
        AbstractQExpander.__init__(self, replace)

    def get_expanded_query(self, q, args=None):
        res=[]
        disamb = disambiguate(q)
        for i,t in enumerate(disamb):
            if t[1] is not None:
                if not self.replace:
                    res.append(t[0])
                x=t[1].name().split('.')[0].split('_')
                if t[0].lower() != (' '.join(x)).lower() or self.replace:
                    res.append(' '.join(x))
            else:
                res.append(t[0])
        return ' '.join(res)


if __name__ == "__main__":
    qe = SenseDisambiguation()
    print(qe.get_model_name())
    print(qe.get_expanded_query('obama family tree'))
    print(qe.get_expanded_query('HosseinFani International Crime Organization'))

    qe = SenseDisambiguation(replace=True)
    print(qe.get_model_name())
    print(qe.get_expanded_query('maryland department of natural resources'))
    print(qe.get_expanded_query('HosseinFani International Crime Organization'))
