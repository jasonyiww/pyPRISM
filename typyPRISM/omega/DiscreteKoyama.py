#!python
from __future__ import division,print_function
from typyPRISM.omega.Omega import Omega
import numpy as np
from math import exp,sin,cos,sqrt
from scipy.optimize import root

class DiscreteKoyama(Omega):
    '''Semi-flexible Koyama-based intra-molecular correlation function
    
    .. note::
        Kevin G. Honnell, John G. Curro, Kenneth S. Schweizer
        Local structure of semiflexible polymer melts
        Macromolecules, 1990, 23 (14), pp 3496–3505
    
    Attributes
    ----------
    sigma: float
        contact distance between these sites (i.e. site diameter)

    l: float
        bond length
        
    length: float
        number of monomers/sites in the chain

    epsilon: float
        bending energy parameter. Must be >0.
        
    lp: float
        persistence length

    cos0: float
        cosine of minimum angle due to 1-3 overlap
    '''
    def __init__(self,sigma,l,length,lp):
        self.sigma   = sigma
        self.length  = length
        self.l       = l
        self.lp      = lp
        self.cos0    = 1 - sigma*sigma/(2.0 * l * l)
        self.value   = None

        if self.lp<4.0/3.0:
            raise ValueError('DiscreteKoyama does not support persistence lengths < 4.0/3.0.')

        self.cos1 = l/lp - 1
        funk = lambda e: self.cos_avg(e) - self.cos1
        result  = root(funk,1.0)

        if result.success != True:
            raise ValueError('DiscreteKoyama initialization failure. Could not solve for bending energy.')

        self.epsilon = result.x
        self.cos2 = self.cos_sq_avg(self.epsilon)
    def cos_avg(self,epsilon):
        '''First moment of bond angle distribution'''
        e = epsilon
        cos0 = self.cos0
        return 1/e  - ( exp(e) + cos0*exp(-e*cos0) )/( exp(e) - exp(-e*cos0) )
    
    def cos_sq_avg(self,epsilon):
        '''Second moment of bond angle distribution'''
        e = epsilon
        cos0 = self.cos0
        cos1 = self.cos_avg(epsilon)
        return (2/e)*cos1 + ( exp(e) - cos0*cos0*exp(-e*cos0) )/( exp(e) - exp(-e*cos0) )
    
    def koyama_kernel(self,k,n):
        '''
        Please see equation 18 of the above reference for details on this calculation.
        '''
        l = self.l
        q = -self.cos1
        p = (3*self.cos2 - 1)/2
        
        D  = n * n * ((1 + q)/(1 - q))**(2.0) 
        D -= n*(1 + (2*q/(1-q)**(3.0)) * (6 + 5*q + 3*q*q) - 4*p/(1-p)*((1 + q)/(1 - q))**(2.0))
        D += 2*q/(1-q)**(4.0) * (4 + 11*q + 12*q*q)
        D -= 4*p/(1-p) * (1 + 8*q/(1-q)**(3.0) + p/(1-p)*((1 + q)/(1 - q))**(2.0))
        D -= q**(n) * 8*q/(1-q)**(3.0) * (n*(1 + 3*q))
        D -= q**(n) * 8*q/(1-q)**(3.0) * ((1 + 2*q + 3*q*q)/(1-q))
        D -= q**(n) * 8*q/(1-q)**(3.0) * (-2*p/(q-p)**(2.0) *(n*(1-q)*(q-p)+2*q*q-q*p-p))
        D -= 6*q**(2*n+2)/(1-q)**(4.0)
        D += p**(n) * (4/(1-p) * (1 + 8*q/(1-q)**(3.0) - ((1+q)/(1-q))**2.0 * (1 - p/(1-p)) ))
        D -= p**(n) * (16*q*q/(1-q)**(3.0) * (1/(q-p)**(2.0))*(q+q*q-2*p))
        D *= 2/3
        
        r2 = n*l*l*((1-self.cos1)/(1+self.cos1) + 2*self.cos1/n * (1-(-self.cos1)**(n))/(1 + self.cos1)**(2.0))
        r4 = r2*r2 + l*l*l*l*D
        
        try:
            C = sqrt(0.5 * (5 - 3*r4/(r2*r2)))
            B = sqrt(C*r2)
            Asq = r2*(1-C)/6 #taking the square root results in many domain errors
        except ValueError as e:
            raise ValueError('Bad chain parameters. (Try reducing epsilon)')
            
        return np.sin(B*k)/(B*k) * np.exp(-Asq*k*k)

    
    def __repr__(self):
        return '<Omega: Koyama>'
    
    def calculate(self,k):
        self.value = np.zeros_like(k)
        
        for i in range(1,self.length-1):
            for j in range(i+1,self.length):
                n = abs(i - j)
                self.value += self.koyama_kernel(k=k,n=n)
        self.value *= 2/self.length
        self.value += 1.0
        
        return self.value
