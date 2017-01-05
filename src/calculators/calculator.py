import scipy.stats as stats


class Calculator:
    '''Class that contains higher level math functions'''

    @staticmethod
    def probability_density(x, mu, sigma):
        '''Calculates probability density'''
        if sigma == 0.0:
            return int(x == mu)
        if x is not None and mu is not None and sigma is not None:
            return 1.0 - stats.norm.cdf(x, mu, sigma)

    @staticmethod
    def welchs_test(mean1, mean2, std1, std2, sampleSize1, sampleSize2):
        '''Calculates `Welch's t-test <https://en.wikipedia.org/wiki/Welch%27s_t-test>`_.
        Used in :class:`AllianceCalculator` :: :func:`win_chance`
        '''
        if std1 == 0.0 or std2 == 0.0 or sampleSize1 <= 0 or sampleSize2 <= 0:
            return float(mean1 > mean2)
        numerator = mean1 - mean2
        denominator = ((std1 ** 2) / sampleSize1 + (std2 ** 2) / sampleSize2) ** 0.5
        return numerator / denominator

    @staticmethod
    def dof(s1, s2, n1, n2):
        '''Calculates degrees of freedom.
        Used in :class:`AllianceCalculator` :: :func:`win_chance`
        '''
        numerator = ((s1**4/n1) + (s2**4/n2)) ** 2
        denominator = (s1**8/((n1**2)*(n1-1))) + (s2**8/((n2**2)*(n2-1)))
        return numerator / denominator
