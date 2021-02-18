# -*- coding: utf-8 -*-
"""

@author: shenjia yi hanchao lei
"""
import numpy as np
import cvxopt as opt
import matplotlib.pyplot as plt

class MeanVariance:
    def __init__(self,returndata):
        self.returndata = returndata

    # produce n random weights that sum to 1
    def rand_weights(self,n):
        k = np.random.rand(n)
        return k/sum(k)

    # return mean and standard deviation of returns for a random portfolio
    def random_portfolio(self,R,Cov,n):
        p = np.asmatrix(R)
        w = np.asmatrix(self.rand_weights(n))
        C = np.asmatrix(Cov)
        mu = w*p
        sigma = np.sqrt(w*C*w.T)
        # This recursion reduces outliers to keep plots pretty
        if sigma > 2:
            return self.random_portfolio(R,Cov,n)
        return mu,sigma

    def optimal_portfolio(self,R,Cov,n):
        N = 100
        mus = [10**(5.0*t/N-1.0) for t in range(N)]
        # Convert to cvxopt matrices
        S = opt.matrix(Cov)
        pbar = opt.matrix(R)
        # Create constraint matrices
        G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
        h = opt.matrix(0.0,(n,1))
        A = opt.matrix(1.0,(1,n))
        b = opt.matrix(1.0)
        opt.solvers.options['show_progress'] = False
        # Calculate efficient frontier weights using quadratic programming
        portfolios = [opt.solvers.qp(mu*S,-pbar,G,h,A,b)['x'] for mu in mus]
        # Calculate risks and returns for frontier
        returns = [np.dot(pbar.T,x)[0][0] for x in portfolios]
        risks = [np.sqrt(np.dot(x.T,S*x))[0][0] for x in portfolios]
        sharpe = list(map(lambda x,y:x/y,returns,risks))
        wt = list(portfolios[sharpe.index(max(sharpe))])
        return wt,returns,risks

    def EfficientFrontier(self):
        R = np.array(self.returndata.mean()).reshape(-1,1)
        Cov = np.asarray(self.returndata.astype(float).cov())
        n = len(R)
        n_portfolios = 1000
        means,stds = np.column_stack([
            self.random_portfolio(R,Cov,n)
            for _ in range(n_portfolios)
            ])
        weights,returns,risks = self.optimal_portfolio(R,Cov,n)
        plt.figure(dpi=800)
        plt.plot(stds, means, 'o')
        plt.ylabel('mean')
        plt.xlabel('std')
        plt.plot(risks, returns, 'y-o')

    def MaxSharpeWeight(self):
        R = np.array(self.returndata.mean()).reshape(-1,1)
        Cov = np.asarray(self.returndata.astype(float).cov())
        n = len(R)
        weights = self.optimal_portfolio(R,Cov,n)[0]
        return weights
