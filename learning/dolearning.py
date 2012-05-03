from competitor_sets.competitor_sets import CompetitorSet, CompetitorSetCollection

# get data (Tobi)
dataobject = CompetitorSetCollection()
print dataobject.get_nsamples() # N
print dataobject.get_sample(17) # yields a competitorset
# TODO: Tobi - put your stuff here


# get featuremethod (Ron)
from features.user_features import FeatureGetter

fg = FeatureGetter()
#print fg.get_features(907345, 907345, 1)
dimension = fg.get_dimension()


# create SGD object, sample different competitorsets, and do learning
from gradientdescent import SGDLearning
import random

sgd = SGDLearning(dimension, fg.get_features)

N = dataobject.get_nsamples()
niter = 10*N
featuredimension = fg.get_dimension()
get_feature_function = fg.get_features
sgd = SGDLearning(featuredimension, get_feature_function)

# TRAINING
# do a couple update steps
for i in range(niter):
    # draw random sample  
    sampleindex = random.randint(1,N)    
    competitorset = dataobject.get_sample(sampleindex)  
    
#    print "iteration", i
#    print "\ttheta", sgd.theta
#    print "\tr", sgd.r
#    print "\tr_hosts", sgd.r_hosts
#    print "\ttrue", competitorset.get_winner()
#    print "\tpredicted", sgd.predict(competitorset)
    
    sgd.update(competitorset, eta=0.1, regularization_lambda=0.1)
    
    
    
# TESTING
errors = 0
correct_non_reject_guesses = 0
total_non_reject_winners = 0
times_guessed_reject = 0
times_guessed_non_reject = 0
for i in range(N):
    #TODO: dirty hack
    competitorset = dataobject.get_sample(i)
    
    pred = sgd.predict(competitorset)
    true = competitorset.get_winner()
    if not pred:
        times_guessed_reject += 1
    else:
        times_guessed_non_reject += 1
    if true:
        total_non_reject_winners += 1
        if true==pred:
            correct_non_reject_guesses += 1
      
    errors += (pred!=true)
    
print 'Training size:', niter
print "Errorrate: %f (%d/%d)"%(errors/float(N), errors, N)
print "non-reject recall: (%s/%s)" %(correct_non_reject_guesses, total_non_reject_winners)
print "Num reject guesses: (%s/%s)" % (times_guessed_reject, N)
print "Num non-reject guesses: (%s/%s)" % (times_guessed_non_reject, N)
