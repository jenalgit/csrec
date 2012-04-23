import cPickle
import numpy as np
import bucketizer

class FeatureGetter():
    """ Generates crossed features for ids

    Requires:
    'user_data.pkl' and 'bucket_dividers.pkl' to be in the current directory'
    
    Attribues:
    bucketizer: a Bucketizer object initialized with 'bucket_dividers.pkl'
    user_data: dictionary of {user_id : user_features} initialized from
    'user_data.pkl'
    """

    def __init__(self):
        self.load_user_features_pkl()
        self.init_bucketizer()
         
    def init_bucketizer(self):
        self.bucketizer = bucketizer.Bucketizer()

    def load_user_features_pkl(self):
        print 'loading user data...'
        self.user_data = cPickle.load(open('user_data.pkl', 'rb'))
        print 'data for %s users loaded' % (len(self.user_data))

    def get_features(self, user_id, host_id, req_id):
        user_features = self.user_data[user_id]
        host_features = self.user_data[host_id]
        return self.bucketizer.cross_bucketized_features(user_features, host_features, [])
    
    def get_dimension(self):
        return self.bucketizer.get_dimension()

def test():
    fg = FeatureGetter()
    print fg.get_features(907345, 907345, 1)
    print fg.get_dimension()

if __name__ == "__main__":
    test()