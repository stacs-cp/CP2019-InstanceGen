#!/usr/bin/env Rscript

# read a parameter definition file in irace's format, output a set of uniformly random configurations
# syntax: ./run-random.R <runDir> <paramFn> <nbConfigurations> [<targetRunner>]
# example: ./random.R random params.irace 100 target-runner

args <- commandArgs(trailingOnly=TRUE)

k <- 1
runDir <- args[k]
k <- k + 1
paramFn <- args[k]
k <- k + 1
nConfs <- as.integer(args[k])
k <- k + 1
if (length(args)>3){
    targetRunner <- args[k]
} else{
    targetRunner <- './target-runner'
}

digits <- 2

source('./utils.R')
source('./readParameters.R')
source('./generation.R')

# read irace parameter definition
parameters <- readParameters(paramFn)

# generation nConfs non-duplicated random configurations
set.seed(123)
tConfs <- sampleUniform(parameters,nConfs,digits)
tConfs <- tConfs[,-c(ncol(tConfs))]

targetRunner <- paste('../',targetRunner,sep='')

# generate command lines
lsCmds <- c()
for (i in c(1:nConfs)){
    candidateId <- i
    instanceId <- i
    seed <- 123
    instance <- 'random'
    conf <- tConfs[i,]
    sConf <- paste(sapply(names(conf), function(param) paste('-',param,' ',conf[[param]],sep='')),collapse=' ')
    cmd <- paste(targetRunner,candidateId,instanceId,seed,instance,sConf,sep=' ')
    lsCmds <- c(lsCmds,cmd)
}

# write command lines to file
cmdsFn <- paste(runDir,'/cmds.txt',sep='')
writeLines(lsCmds,con<-file(cmdsFn))
close(con)
