# import numpy as np
# import scipy as sp
import scipy.stats as stats


class Calculator:

    def probability_density(self, x, mu, sigma):
        if sigma == 0.0:
            return int(x == mu)
        if x is not None and mu is not None and sigma is not None:
            return 1.0 - stats.norm.cdf(x, mu, sigma)

    def welchs_test(self, mean1, mean2, std1, std2, sampleSize1, sampleSize2):
        if std1 == 0.0 or std2 == 0.0 or sampleSize1 <= 0 or sampleSize2 <= 0:
            return float(mean1 > mean2)
        numerator = mean1 - mean2
        denominator = ((std1 ** 2) / sampleSize1 + (std2 ** 2) / sampleSize2) ** 0.5
        return numerator / denominator

    def dof(self, s1, s2, n1, n2):
        numerator = ((s1**4/n1) + (s2**4/n2)) ** 2
        denominator = (s1**8/((n1**2)*(n1-1))) + (s2**8/((n2**2)*(n2-1)))
        return numerator / denominator
