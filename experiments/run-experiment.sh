#!/bin/bash

# setup an tuning/random-search experiment for a problem class
# syntax: ./run-experiment.sh <experimentDir> <problem> <maxint-for-generator> <search-method (irace/random)> <budget> <number-of-cores> <problem-type (decision/optimisation)> <scale (log/linear)> <environment (local/cluster-local/cluster-remote)> <seed>
# example: ./run-experiment.sh maxint-50-log 002-TemplateDesign 50 irace 1000 2 optimisation log local 123



if [ $# -ne 10 ]
then
	echo "USAGE:  ./run-experiment.sh <expDir> <problem> <maxint> <irace/random> <budget> <parallel> <decision/optimisation> <log/linear> <local/cluster-local/cluster-remote> <seed>"
	echo "# example:  ./run-experiment.sh maxint-50-log 002-TemplateDesign 50 irace 1000 2 optimisation log local 123"
	exit -1
fi

expDir=$1
problem=$2
maxint=$3
setting=$4
budget=$5
parallel=$6
version=$7
scale=$8
env=$9
seed=${10}

current_dir=$(pwd)
base_dir=$(dirname $current_dir)
outDir="$expDir/$problem"

mkdir -p $outDir
cp ../models/$problem.essence $outDir/model.essence

scriptDir="../scripts"
cp $scriptDir/*.txt $scriptDir/*.R $scriptDir/instances $scriptDir/*.sh $scriptDir/target-runner $scriptDir/wrapper.py $scriptDir/run-$setting.pbs $outDir

if [ $version == "decision" ]; then
    cp $scriptDir/instance-options-decision.txt $outDir/instance-options.txt
else
    cp $scriptDir/instance-options-optimisation.txt $outDir/instance-options.txt
fi

d=$PWD
cd $outDir

runDir=Seed${seed}-$setting-$budget
./prepare.sh $runDir $maxint $scale $env

pbsFn="run-$setting.pbs"
sed -i -e "s,<seed>,$seed,g" $pbsFn
sed -i -e "s,<runEnv>,$env,g" $pbsFn
sed -i -e "s,<baseDir>,$base_dir,g" $pbsFn
sed -i -e "s,<workingDir>,$current_dir/$expDir/$problem/,g" $pbsFn
sed -i -e "s/<runDir>/$runDir/g" $pbsFn
sed -i -e "s/<budget>/$budget/g" $pbsFn
sed -i -e "s/<parallel>/$parallel/g" $pbsFn

if [ $env == "cluster-remote" ];
then
	cmd="qsub -N $problem-$seed-$maxint-$setting-$budget run-$setting.pbs; cd .."
	echo $cmd
	eval $cmd
else
	cmd="./run-$setting.pbs; cd $d"
	echo $cmd
	eval $cmd
fi



