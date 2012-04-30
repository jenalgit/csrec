# -*- coding: utf-8 -*-
"""
Realization of the update equations in derivation.pdf
Here, for the case with personalized host parameters theta_h
We assume the following format:
    - update(old_params, competitorset) -> new_params
    - get_feature(surferID, hostID, couchrequestID) -> 1D numpy array
    - competitorset structure: dict with keys hostID, list_surfers [(surferID, requestID), ...], winner (surferID or None if all rejected)

TODO:
    - update similarly to nonpersonalized version
    - rademacher hash 

@author: Tim
"""

import numpy as np
from IPython import embed

def inthash(x,y,N): # take this one
    a = (x * 0x1f1f1f1f) ^ y
    a = (a ^ 61) ^ (a >> 16)
    a = a + (a << 3)
    a = a ^ (a >> 4)
    a = a * 0x27d4eb2d
    a = a ^ (a >> 15)
    return a%N  

class SGDLearningPersonalized:

    def __init__(self, featuredimension, get_feature_function, memory_for_personalized_parameters, theta=None, r=None, r_hosts=None, theta_hosts=None):
        self.featuredimension = featuredimension
        self.theta = theta if theta else 0.2*(np.random.rand(featuredimension+1) - 0.5) # +1 to learn bias term
        self.r = r if r else 0.0
        #r_hosts = np.zeros(nhosts) # do I need dictionary here: hostID -> param?
        self.r_hosts = r_hosts if r_hosts else {}
        self.get_feature = get_feature_function
        
        if theta_hosts!=None:
            self.theta_hosts = theta_hosts
            self.nelements = len(self.theta_hosts)
        else:
            # build large array that the personalized host parameters are hashed into
            self.nelements = memory_for_personalized_parameters * 1000000 / 8 # assuming 64bit floats, and memory in MB
			#TODO: does it make sense to initialize this randomly?
            self.theta_hosts = 0.2*(np.random.rand(self.nelements) - 0.5) #np.zeros(self.nelements)
    
    def get_score(self, feature, theta_h):
        return np.exp(np.dot(self.theta + theta_h,feature))
        
    def get_rejectscore(self, hostID):
        # if we don't have a r_host yet create one with param zero
        if not self.r_hosts.has_key(hostID):
            self.r_hosts[hostID] = 0.0
            
        return np.exp(self.r + self.r_hosts[hostID])

    def get_hostparameters(self, hostID):
        indizes = [inthash(hostID,i,self.nelements) for i in range(self.featuredimension)]
        theta_h = self.theta_hosts[indizes]
        return theta_h
   
    def predict(self, competitorset):
        # used for inference later and to evaluate error on testset
        hostID = competitorset.get_hostID()        
        
        # if we don't have a r_host yet create one with param zero
        if not self.r_hosts.has_key(hostID):
            self.r_hosts[competitorset.get_hostID()] = 0.0
        
        #features = [self.get_feature(surferID,hostID,requestID) for (surferID, requestID) in competitorset.get_surferlist()] # before without bias
        #features = [np.append(self.get_feature(surferID,hostID,requestID),np.ones(1)) for (surferID, requestID) in competitorset.get_surferlist()] # with appended 1 feature for bias term
        features = [np.hstack((self.get_feature(surferID,hostID,requestID),np.ones(1)*(surferID==competitorset.get_winner()), np.ones(1))) for (surferID, requestID) in competitorset.get_surferlist()] # CHEAT TODO REMOVE
        #features = [np.append(2*(np.ones(1)*(surferID==competitorset.get_winner()))-1, np.ones(1)) for (surferID, requestID) in competitorset.get_surferlist()] # w Bias CHEAT TODO REMOVE
        
        # get personalized hostparameters
        #theta_h = self.get_hostparameters(hostID)
        indizes = [inthash(hostID,i,self.nelements) for i in range(self.featuredimension)]
        theta_h = self.theta_hosts[indizes]
        #print "PERS PARAMS", hostID, theta_h # TODO remove
        
        scores = [self.get_score(f, theta_h) for f in features]
        rejectscore = self.get_rejectscore(hostID)
        
        maxsurfer = np.argmax(scores)
		# TODO comment out	
        #print "rejectscore", rejectscore
        #print "maxsurferscore", scores[maxsurfer]
        #print ""
        if rejectscore>scores[maxsurfer]:
            return None
        else: # return surferID of winner
            return competitorset.get_surferlist()[maxsurfer][0]
        
    
    def update(self, competitorset, eta=0.01, lambda_winner=0.1, lambda_reject=1.0):
        hostID = competitorset.get_hostID() 
        # if we don't have a r_host yet create one with param zero
        if not self.r_hosts.has_key(hostID):
            self.r_hosts[hostID] = 0.0        
        
        # get features, scores, and probabilities
        #features = [self.get_feature(surferID,hostID,requestID) for (surferID, requestID) in competitorset.get_surferlist()] # before without bias
        #features = [np.append(self.get_feature(surferID,hostID,requestID),np.ones(1)) for (surferID, requestID) in competitorset.get_surferlist()] # with appended 1 feature for bias term
        features = [np.hstack((self.get_feature(surferID,hostID,requestID),np.ones(1)*(surferID==competitorset.get_winner()), np.ones(1))) for (surferID, requestID) in competitorset.get_surferlist()] # CHEAT TODO REMOVE
        #features = [np.append(2*(np.ones(1)*(surferID==competitorset.get_winner()))-1, np.ones(1)) for (surferID, requestID) in competitorset.get_surferlist()] # w Bias CHEAT TODO REMOVE

                
        # get personalized hostparameters
        #theta_h = self.get_hostparameters(hostID) 
        indizes = [inthash(hostID,i,self.nelements) for i in range(self.featuredimension)]
        theta_h = self.theta_hosts[indizes]
        
        scores = [self.get_score(f, theta_h) for f in features]
        rejectscore = self.get_rejectscore(hostID)
        normalizer = float(np.sum(scores) + rejectscore)
        probabilities = [s/normalizer for s in scores]
        rejectprobability = rejectscore / normalizer
        
        # update params based on ground truth
        if competitorset.get_winner()==None:
            # gt -> all got rejected
            temp = [p*f for (p,f) in zip(probabilities,features)]
            self.theta =  (1 - eta * lambda_winner) * self.theta - eta * np.sum(temp, axis=0)
            #self.r = self.r - eta * (rejectprobability - 1)
            self.r = (1 - eta * lambda_reject) * self.r - eta * (rejectprobability - 1)
            self.r_hosts[hostID] =  (1 - eta * lambda_reject) * self.r_hosts[hostID] - eta * (rejectprobability - 1) 

            # update of personalized host parameters
            self.theta_hosts[indizes] = (1 - eta * lambda_winner) * theta_h - eta * np.sum(temp, axis=0)
        else:
            # there was a winner
            winneridx = zip(*competitorset.get_surferlist())[0].index(competitorset.get_winner())
            
            temp = [p*f for (p,f) in zip(probabilities,features)]
            self.theta = (1 - eta * lambda_winner) * self.theta - eta * (np.sum(temp, axis=0) - features[winneridx])
            #self.r = self.r - eta * rejectprobability
            self.r = (1 - eta * lambda_reject) * self.r - eta * rejectprobability
            self.r_hosts[hostID] =  (1 - eta * lambda_reject) * self.r_hosts[hostID] - eta * rejectprobability 

            # update of personalized host parameters
            self.theta_hosts[indizes] = (1 - eta * lambda_winner) * theta_h - eta * (np.sum(temp, axis=0) - features[winneridx])
    


if __name__=='__main__':
    print 'Preliminary testing of gradient descent update equations:'
    
    # build fake features
    def get_feature(surferID, hostID, couchrequestID):
        feat = np.zeros(3)
        if surferID==cs.get_winner():
            feat[0] = 1 # later try 2,1 
        else: 
            feat[0] = -1
        feat[1] = 2
        
        if hostID==0: # to test out whether the host params pick up the signal
            return -feat
        else:
            return feat
    
#    competitorset = {
#        'hostID': 0,
#        'list_surfers': [(1,1), (2,2), (3,3)],
#        'winner': 3, # later try None
#    }
    #print competitorset
    class CompetitorSet:
        def get_hostID(self):
            return 0
            
        def get_surferlist(self):
            return [(1,1), (2,2), (3,3)]
        
        def get_winner(self):
            return 3
            
    class CompetitorSet2: # different winner with different features
        def get_hostID(self):
            return 1
            
        def get_surferlist(self):
            return [(1,1), (2,2), (3,3)]
        
        def get_winner(self):
            return 2 
            
    class CompetitorSet3: # reje!=Nonect Host
        def get_hostID(self):
            return 2
            
        def get_surferlist(self):
            return [(1,1), (2,2), (3,3)]
        
        def get_winner(self):
            return None
    
    competitorset = CompetitorSet()
    competitorset2 = CompetitorSet2()
    competitorset3 = CompetitorSet3()
    competitorsets = [competitorset, competitorset, competitorset, competitorset2, competitorset3]
    
    
    featuredimension = 3
    get_feature_function = get_feature # here Ron's function should go
    memsize = 1 #MB
    #sgd = SGDLearningPersonalized(featuredimension, get_feature_function, memsize)
    theta = np.arange(3)
    r = 17
    r_hosts = {}
    theta_hosts = np.random.rand(20) - 0.5
    sgd = SGDLearningPersonalized(featuredimension, get_feature_function, memsize, theta=theta, r=r, r_hosts=r_hosts, theta_hosts=theta_hosts)    
    
    niter = 1000
    
    # do a couple update steps
    for i in range(niter):
        cs = competitorsets[i%len(competitorsets)] # iterate throught different competitorsets  
        
        print "iteration", i
        print "\ttheta", sgd.theta
        theta_h = sgd.get_hostparameters(cs.get_hostID())
        print "\ttheta_host", theta_h
        print "\ttheta_total", theta_h + sgd.theta
        winnerfeat = get_feature(cs.get_winner(), cs.get_hostID(), cs.get_winner())
        print "\twinnerfeat", winnerfeat
        print "\tr", sgd.r
        print "\tr_hosts", sgd.r_hosts
        print "\ttrue", cs.get_winner()
        print "\tpredicted", sgd.predict(cs)
        
        sgd.update(cs, eta=0.1, regularization_lambda=0.1)
        
    