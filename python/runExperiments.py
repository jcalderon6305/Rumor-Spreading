# runExperiments
import utilities
import buildGraph
import infectionModels

'''Runs a spreading algorithm over a real dataset. Either pramod's algo (deterministic) or message passing (ours)'''    
def runDataset(filename, min_degree, trials, max_time=100, max_infection = -1):
    # Run dataset runs a spreading algorithm over a dataset. 
    # Inputs:
    #
    #       filename:               name of the file containing the data
    #       min_degree:             remove all nodes with degree lower than min_degree
    #       trials:                 number of trials to run
    #       max_time(opt):          the maximum number of timesteps to use
    #       max_infection(opt):     the maximum number of nodes a node can infect in any given timestep
    #
    # Outputs:
    #
    #       p:                      average proportion of nodes reached by the algorithm 
    #       num_infected:           total number of nodes infected by the algorithm
    #
    # NB: If max_infection is not set, then we'll run the deterministic algorihtm. Otherwise, it's the message passing one.
    
    adjacency = buildGraph.buildDatasetGraph(filename, min_degree)
    # print(adjacency)
    num_nodes = len(adjacency)
    num_true_nodes = sum([len(item)>0 for item in adjacency])
    print('nonzero nodes:',num_true_nodes)
    num_infected = 0
    p = 0
    pd_jordan = [0 for i in range(max_time)]
    pd_rumor = [0 for i in range(max_time)]
    pd_ml = [0 for i in range(max_time)]
    
    stepsize = 5;
    # max_infection+1 is the degree of the tree
    max_nodes = int(infectionModels.N_nodes(max_time,max_infection+1))
    bins = [i for i in range(1,max_nodes+stepsize+1,stepsize)]
    jordan_found = [0 for i in range(len(bins))]
    jordan_count = [0 for i in range(len(bins))]
    rumor_found = [0 for i in range(len(bins))]
    rumor_count = [0 for i in range(len(bins))]
    
    for trial in range(trials):
        # if trial % 20 == 0:
        print('Trial ',trial, ' / ',trials)
        while True:
            source = random.randint(0,num_nodes-1)
            if len(adjacency[source]) > 0:
                break
        if max_infection == -1:      # i.e. we're running the deterministic version
            num_infected, infection_pattern = infectionModels.infect_nodes_deterministic(source,adjacency)
        else:
            num_infected, infection_pattern, who_infected, results = infectionModels.infect_nodes_adaptive_diff(source,adjacency,max_time,max_infection,stepsize)
            # unpack the results
            jordan_results, rumor_results, ml_correct = results
            jordan_bins, jordan_instances, jordan_detected, jordan_correct = jordan_results
            rumor_bins, rumor_instances, rumor_detected, rumor_correct = rumor_results
            
            pd_jordan = [i+j for (i,j) in zip(pd_jordan, jordan_correct)]
            jordan_found = [i+j for (i,j) in zip(jordan_found,jordan_detected)]
            jordan_count = [i+j for (i,j) in zip(jordan_count,jordan_instances)]
            pd_rumor = [i+j for (i,j) in zip(pd_rumor, rumor_correct)]
            rumor_found = [i+j for (i,j) in zip(rumor_found,rumor_detected)]
            rumor_count = [i+j for (i,j) in zip(rumor_count,rumor_instances)]
            
            pd_ml = [i+j for (i,j) in zip(pd_ml, ml_correct)]
            
            # write the infected subgraph to file
            filename = 'infected_subgraph_'+str(trial)
            exportGraph.export_gexf(filename,who_infected,source,infection_pattern,adjacency)
            
        p += float(num_infected) / num_true_nodes
    p = p / trials
    pd_jordan = [float(i)/j for (i,j) in zip(jordan_found, jordan_count) if j>0]
    pd_rumor = [float(i)/j for (i,j) in zip(rumor_found, rumor_count) if j>0]
    pd_ml = [float(i) / trials for i in pd_ml]
    return p, num_infected, pd_jordan, pd_rumor, pd_ml
    
'''Run a random tree'''    
def run_randtree(trials, max_time, max_infection, degrees_rv, method=0, known_degrees=[]):
    # Run dataset runs a spreading algorithm over a dataset. 
    # Inputs:
    #
    #       trials:                 number of trials to run
    #       max_time:               the maximum number of timesteps to use
    #       degrees_rv:              remove all nodes with degree lower than min_degree
    #       method:                 which approach to use: 0 = regular spreading to all neighbors, 
    #                                                      1 = alternative spreading (VS chosen proportional to degree of candidates) 
    #                                                      2 = pre-planned spreading
    #                                                      3 = Old adaptive diffusion (i.e. line algorithm)
    #
    # Outputs:
    #
    #       p:                      average proportion of nodes reached by the algorithm 
    #       num_infected:           total number of nodes infected by the algorithm
    #
    # NB: If max_infection is not set, then we'll run the deterministic algorihtm. Otherwise, it's the message passing one.
    
    pd_ml = [0 for i in range(max_time)] # Maximum likelihood
    pd_rc = [0 for i in range(max_time)] # Rumor centrality
    pd_jc = [0 for i in range(max_time)] # Jordan centrality
    pd_rand_leaf = [0 for i in range(max_time)]
    avg_num_infected = [0 for i in range(max_time)]
    
    for trial in range(trials):
        if trial % 50 == 0:
            print('Trial ',trial, ' / ',trials-1)
        source = 0
        if method == 0:
            num_infected, infection_pattern, who_infected, ml_correct = infectionModels.infect_nodes_adaptive_diff_irregular_tree(source, max_time, max_infection, degrees_rv)
        elif method == 1:
            num_infected, infection_pattern, who_infected, ml_correct = infectionModels.infect_nodes_adaptive_diff_irregular_tree_alt(source, max_time, max_infection, degrees_rv)
        elif method == 2:
            num_infected, infection_pattern, who_infected, ml_correct, rand_leaf_correct, known_degrees = infectionModels.infect_nodes_adaptive_planned_irregular_tree(source, max_time, max_infection, degrees_rv, known_degrees)
            pd_rand_leaf = [i+j for (i,j) in zip(pd_rand_leaf, rand_leaf_correct)]
        elif method == 3:
            num_infected, who_infected, results = infectionModels.infect_nodes_line_adaptive_diff(source, max_time, max_infection, degrees_rv)
            pd_jc = [i+j for (i,j) in zip(pd_jc, results[0])]
            pd_rc = [i+j for (i,j) in zip(pd_rc, results[1])]
            # We don't actually compute the ML estimate here because it's computationally challenging
            ml_correct = pd_ml 
        # unpack the results
        pd_ml = [i+j for (i,j) in zip(pd_ml, ml_correct)]
        avg_num_infected = [i+j for (i,j) in zip(avg_num_infected, num_infected)]
        
    pd_ml = [float(i) / trials for i in pd_ml]
    pd_rand_leaf = [float(i) / trials for i in pd_rand_leaf]
    avg_num_infected = [ float(i) / trials for i in avg_num_infected]
    
    if method == 3:
        pd_rc = [float(i) / trials for i in pd_rc]
        pd_jc = [float(i) / trials for i in pd_jc]
        return avg_num_infected, pd_rc, pd_jc
        
    return avg_num_infected, pd_ml, pd_rand_leaf