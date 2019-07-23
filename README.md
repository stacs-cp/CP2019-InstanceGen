This repository contains the source code and experiment results for the paper:

*Özgür Akgün, Nguyen Dang, Ian Miguel, Andras Z. Salamon and Christopher Stone. **Instance Generation via Generator Instances**. CP2019*


#### Structure
- `models`: Essence speficiation of 5 problem classes used in our paper. They are taken from [CSPLib](http://www.csplib.org/).
- `scripts`: all scripts & files needed for setting up an experiment.
- `experiments`: the actual script to setup and launch an experiment
- `experiments/results`: all results for reported in the paper


#### Usage
To launch an experiment, simply use the script `experiments/run-experiment.sh`. See `experiments/examples.sh` for some examples on how to use the script.
