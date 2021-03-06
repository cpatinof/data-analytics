# -*- coding: utf-8 -*-
"""
Created on Fri May  4 14:05:25 2018

@author: mrestrepo
@company: Yuxi Global (www.yuxiglobal.com)


TODO: 
    - Extension multi-class classifiers
    - Extension to Boosted Tree models 
    
"""
import numpy as np 

def rf_explain( rfc, X ) : 
    """
    Arguments : 
        - rfc - a sklearn.ensemble.RandomForest already trained on a 
                binary classification task.
        - X   - a data-frame  of features shape (N, p)
            all features must be numeric (p features)
            
    Returns (p0, E) 
        - p0 : float - the a prioriy  
        - E : np.array of shape (N, p) containing the explanations
    """
    
    assert_impl_limitations( rfc  )
    X = ensure_np_array_32( X )
    
    n = X.shape[0]    
    explanations = np.zeros( ( n, rfc.n_features_ ) )
    
    p0_sum = 0.0
    for cls in rfc.estimators_ :
        E, p0 = tree_explain( cls, X )
        explanations[:] += E
        p0_sum  += p0
        
        
    n_est = len(rfc.estimators_)
    #%%
    return (explanations / n_est), (p0_sum / n_est)  
    
def tree_explain( cls, X ) : 
    """
    Arguments : 
        - cls - a sklearn.tree.tree.DecisionTreeClassifier already trained
            on a binary classification task 
        - X   - a data-frame or np.array of features shape (N, p)
        all features must be numeric (p features)
        
    Returns (p0, E) 
        - p0 : float - the a prioriy  
        - E : np.array of shape (N, p) containing case-by-case 
        explanations 
        - 
    """
    
    assert_impl_limitations( cls )
    Xa = ensure_np_array_32( X )                
    n = Xa.shape[0] # number of cases for evaluation
    
    #%% Compute constant  probability of class 1 for every node
    tree = cls.tree_    
    node_probs_c1 =  (tree.value[:,0, 1]) / ( tree.value[:,0,:].sum(axis=1))
    
    
    explanations = np.zeros( ( n, cls.n_features_) )
    #explanations[:, cls.n_features_] = a_priori_prob 
    
    dp = tree.decision_path( Xa )
    feature = tree.feature
    
    # the following loop should  be implemented in cython for efficiency! 
    
    for i in range(n) :  # run over evaluation cases 
               
        #path_len = len( path )        
        prev_feat = feature[0]  
        prev_prob = node_probs_c1[0]
        path = dp[i,:].indices  # indices of nodes in this case's path
        
        for j in path[ 1: ] :            
            
            cur_prob = node_probs_c1[ j ]
            
            delta_p = cur_prob - prev_prob                        
            explanations[i, prev_feat ] += delta_p 
            
            prev_prob = cur_prob    
            prev_feat = feature[j]
            
    a_priori_prob = node_probs_c1[0]
    #%%    
    return explanations, a_priori_prob     
    #%%
    
def as_pyplot_figure( exp, p0, feat_names, instance_desc ) :
    """Following lime.explanation.Explanation.as_pyplot_figure, almost verbatim"""
    import matplotlib.pyplot as plt
    
    #exp = self.as_list(label=label, **kwargs)
    exp = list( zip( feat_names, exp ) ) 
    fig = plt.figure( dpi=300)
    vals = [x[1] for x in exp]
    names = [x[0] for x in exp]
    vals.reverse()
    names.reverse()
    colors = ['green' if x > 0 else 'red' for x in vals]
    pos = np.arange(len(exp)) + .5
    plt.barh(pos, vals, align='center', color=colors)
    plt.yticks(pos, names)
    plt.xlabel('Contribution to probability of positive class')
    
    title = 'Explanation for %s (Predicted prob.=%.3f)' % (instance_desc, p0 + sum(vals) )
    
    plt.title(title)
    return fig
	
def assert_impl_limitations( cls )  :
    #%%    
    assert cls.n_classes_ == 2, ( "Explanation method implemented for binary "
            "classifiers only. However, generalization to any number of classes"
            " is pretty straigh forward! Please contribute!" )
    
    assert cls.n_outputs_ == 1, ("Explanation method implemented for single "
                                 "output classifiers only" )
    #%%
    
def ensure_np_array_32( X ) : 
    
    if type(X) != np.ndarray : 
        X = X.values
    
    if X.dtype != np.float32 : 
        X = X.astype( np.float32 )
    
    return X
    
