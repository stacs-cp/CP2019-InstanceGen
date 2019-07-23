#!/bin/bash

# here are some examples of using the script run-experiment.sh to launch tuning/random-search experiments

# example 1: use irace with a budget of 1000 runs to generate instances for the TemplateDesign problem (see ../models/ for the Essence specification of the problem)
# properties of this experiment:
# - Search method: irace
# - MAXINT for the generator: 50
# - irace's random seed: 123
# - Number of cores used (in parallel, by irace): 2
# - Parameter scale (used by irace): log-scale
# - This is run locally on a single computer (instead of on the cluster, where a .pbs script file will be generated and submitted)
# - All tuning results are saved in folder maxint-50-log/002-TemplateDesign/Seed123-irace-1000
./run-experiment.sh maxint-50-log 002-TemplateDesign 50 irace 1000 2 optimisation log local 123


# example 2: same as example 1, but with random search instead of irace, i.e., 1000 random configurations are generated and instances created by these configurations are recorded
./run-experiment.sh maxint-50-log 002-TemplateDesign 50 random 1000 2 optimisation log local 123
