# reject baseline - always rejecting is not too bad (~15% error on small testset)
from mpi.mpi_imports import *

def reject_baseline_test_predictionerror(data):
  nones = 0
  N = data.get_nsamples()
  for i in range(N):
    cs = data.get_sample(i)
    if cs.get_winner()==None:
      nones += 1
  accuracy = nones / float(N)
  return accuracy
  
def reject_baseline_test_predictionerror_mpi(data):
  nones = 0
  N = data.get_nsamples()
  for i in range(comm_rank, N, comm_size):
    cs = data.get_sample(i)
    if cs.get_winner()==None:
      nones += 1
  safebarrier(comm)
  nones = comm.allreduce(nones)    
  accuracy = nones / float(N)
  return accuracy  
  

  
def reject_baseline_test_meannormalizedwinnerrank(data):
  sumnrank = 0.0
  N = data.get_nsamples()
  for i in range(N):
    competitorset = data.get_sample(i)
    true = competitorset.get_winner()
    if true==None:
      nrank = 0
    else:
      n = len(cand) 
      nrank = float(n)/(2*float(n-1)) # Tim thinks it works out like this mathematically
    sumnrank += nrank
    
  meannrank= sumnrank/float(N)  
  return meannrank
  
  
def reject_baseline_test_meannormalizedwinnerrank_mpi(data):
  sumnrank = 0.0
  N = data.get_nsamples()
  for i in range(comm_rank, N, comm_size):
    competitorset = data.get_sample(i)
    true = competitorset.get_winner()
    if true==None:
      nrank = 0
    else:
      n = len(cand) 
      nrank = float(n)/(2*float(n-1)) # Tim thinks it works out like this mathematically
    sumnrank += nrank
  
  safebarrier(comm)
  sumnrank = comm.allreduce(sumnrank)   
  meannrank= sumnrank/float(N)  
  return meannrank
  
