#!/bin/bash

# generate all problem-specific neccessary files for a tuning/random-search experiment
# syntax: ./prepare.sh <runDir> <maxint-for-generator-spec> <scale (linear/log)> <environment (local/cluster)>
# example: ./prepare.sh Seed0-irace-1000 50 linear local

runDir=$1
maxint=$2
scale=$3
env=$4

if [[ $env =~ "cluster" ]]
then
    module load gcc
	module load R
fi

options=""
if [ ! -z "$maxint" ]; then
    options="--MAXINT $maxint"
fi

# create generator's spec and irace's param file
conjure parameter-generator model.essence --essence-out generator.essence $options
mv generator.essence.irace params.irace
echo "" >>params.irace # add EOL into params.irace, otherwise irace will complain

# transform params.irace if log-scale is used
if [ "$scale" == "log" ]; then
    sed -i -e "s/ i / i,log /g" params.irace 
fi
Rscript read-log-parameters.R params.irace

# generate eprime models
mkdir -p models
mkdir -p generator-models
conjure modelling -ac model.essence
cp conjure-output/model000001.eprime models/model.eprime
conjure modelling -ac generator.essence
cp conjure-output/model000001.eprime generator-models/model.eprime

# copy all to the folder where the experiment is run
mkdir $runDir
cp -r model* generator* instance-options.txt $runDir
