#!/usr/bin/env python

# wrapper for irace call to a run for generating instances from Conjure specification

import os
import sys
import subprocess
import random
import time
import glob
import shlex
import re
import json
from shutil import copyfile

# conjure solve options for the target solver, overriden by instance-options.txt
instanceOptions = {}
instanceOptions['savilerowOptions'] = "-preprocess None -timelimit 300000"
instanceOptions['solverTimeLimit'] = 180 # in seconds
instanceOptions['solverNodeLimit'] = 1000000
instanceOptions['solverMinTime'] = 0 # in seconds, 0 means there is no lower bound
instanceOptions['solverMinNode'] = 1000
instanceOptions['solverTimeLimitPrefix'] = '-cpulimit ' # minion
instanceOptions['solverNodeLimitPrefix'] = '-nodelimit ' # minion
instanceOptions['solverRandomSeedArg'] = '-randomseed ' # minion
instanceOptions['solverFlags'] = '-varorder domoverwdeg -valorder random -restarts' # minion
instanceOptions['solver'] = 'minion'
instanceOptions['nEvaluations'] = 5
instanceOptions['essenceModel'] = './model.essence'
instanceOptions['eprimeModel'] = './models/model.eprime'

# generator options
generatorOptions = {}
generatorOptions['savilerowOptions'] = '-timelimit 120000'
generatorOptions['solverFlags'] = '-varorder domoverwdeg -valorder random -randomiseorder -timelimit 300'
generatorOptions['solverRandomSeedArg'] = '-randomseed '
generatorOptions['essenceModel'] = './generator.essence'
generatorOptions['eprimeModel'] = './generator-models/model.eprime'


def readFile(fn):
    lsLines = []
    with open(fn,'rt') as f:
        lsLines = [line.rstrip('\n') for line in f]
        
    return lsLines


def searchString(s, lsStrs):
    lsOut = []
    for line in lsStrs:
        if s in line:
            lsOut.append(line)
    return lsOut



def runCmd(cmd,outFn=None):
    lsCmds = shlex.split(cmd)
    p = subprocess.run(lsCmds,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = p.stdout.decode('utf-8')
    if outFn is not None:
        with open(outFn,'wt') as f:
            f.write(output)
    return output, p.returncode


def paramsToDict(params):
    paramDict = {}
    for i in range(0,len(params),2):
        paramDict[params[i][1:]] = params[i+1]
    return paramDict


def deleteFile(fn):
    if isinstance(fn,list): # delete file list
        for name in fn:
            if isinstance(name,list):
                deleteFile(name)
            elif os.path.isfile(name):
                os.remove(name)
    else: # delete by pattern
        lsFn = glob.glob(fn)
        for fn in lsFn:
            os.remove(fn)


def call_conjure_solve(conjureOptions, paramFile, essenceModelFn, eprimeModelFn, nodeLimit=0, timeLimit=0, rndSeed=None, modelDir='models/'):
    baseFn = os.path.basename(paramFile).split('.')[0]

    # conjure solve command line
    solverOptions = ''
    if timeLimit > 0:
       solverOptions += conjureOptions['solverTimeLimitPrefix'] + str(timeLimit)
    if nodeLimit > 0:
        solverOptions += ' ' + conjureOptions['solverNodeLimitPrefix'] + str(nodeLimit)
    if rndSeed is not None:
        solverOptions += ' ' + conjureOptions['solverRandomSeedArg'] + str(rndSeed) 
    cmd = 'conjure solve ' + essenceModelFn + ' ' + paramFile + ' -o ' + modelDir \
            + " --savilerow-options '" + conjureOptions['savilerowOptions'] + "'" \
            + " --use-existing-models=" + eprimeModelFn + " --copy-solutions=no "\
            + "--solver-options '" + solverOptions + " " + conjureOptions['solverFlags'] + "'"\
            + " --solver=" + conjureOptions['solver']
    print("\nCalling conjure")
    print(cmd)
    cmdOutput, returncode = runCmd(cmd)
    print(cmdOutput)
    time.sleep(3) # wait for a few seconds so SR can finish writing down the info file

    # if returncode!=0, check if it is because SR is out of memory
    if ('GC overhead limit exceeded' in cmdOutput) or ('OutOfMemoryError' in cmdOutput) or ('insufficient memory' in cmdOutput):
        SRMemOut = 1
    else:
        SRMemOut = 0

    baseFn = modelDir + '/' + eprimeModelFn.split('.')[0] + '-' + baseFn
    print(baseFn)
    infoFn = baseFn + '.eprime-info'
    inforFn = baseFn + '.eprime-infor'
    minionFn = baseFn + '.eprime-minion'
    dimacsFn = baseFn + '.eprime-dimacs'
    eprimeSolutionFn = glob.glob(baseFn + '*.eprime-solution')
    solutionFn = glob.glob(baseFn + '*.solution')

    # rename infoFn so that it includes random seed
    if (rndSeed is not None) and (os.path.exists(infoFn)):
        newInfoFn = baseFn + '-seed_' + str(rndSeed) + '.eprime-info'
        os.rename(infoFn, newInfoFn)
        infoFn = newInfoFn
    
    return [SRMemOut,infoFn, inforFn, minionFn, solutionFn, dimacsFn, cmd]


def parseSRInfoFile(SRMemOut,fn,nodeLimit=0):
    #header = ','.join(['instance','model','SRTimeOut','SRTime','solverTimeOut','solverTime','solverNodeOut','nNodes','sat'])


    ls = os.path.basename(fn).split('.')[0].split('-')
    model = ls[0]
    # remove random seed in instance name
    if 'seed' in ls[-1]:
        ls = ls[0:-1]
    instance = '-'.join(ls[1:])

    SRTime = ''
    solverTimeOut = ''
    solverTime=''
    solverNodeOut=''
    solverMemOut=''
    nNodes=''
    sat=''
    
    
    # if SR is out of memory, there will be no info file
    if SRMemOut==1:
        SRTimeOut = ''
        return instance,model,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat

    lsLines = readFile(fn)
    
    SRTimeOut = 0
    if len(searchString('SavileRowTimeOut:', lsLines)) > 0:
        SRTimeOut = int(searchString('SavileRowTimeOut:',lsLines)[0].split(':')[1].strip())
    if len(searchString('SavileRowClauseOut:', lsLines))>0:
        SRClauseOut = int(searchString('SavileRowClauseOut:',lsLines)[0].split(':')[1].strip())
    SRTimeOut = SRTimeOut | SRClauseOut



    if SRTimeOut == 0:
        SRTime = searchString('SavileRowTotalTime:',lsLines)[0].split(':')[1].strip()

        ls = searchString('SolverMemOut:',lsLines)
        if len(ls) > 0:
            solverMemOut = int(searchString('SolverMemOut:',lsLines)[0].split(':')[1].strip())
        else:
            solverMemOut = 0
        
        if solverMemOut == 0:
            solverTimeOut = int(searchString('SolverTimeOut:',lsLines)[0].split(':')[1].strip())
            
            if solverTimeOut == 0:
                solverTime = float(searchString('SolverTotalTime:',lsLines)[0].split(':')[1].strip())
                
                ls = searchString('SolverNodes:',lsLines)
                if len(ls) > 0:
                    nNodes = float(ls[0].split(':')[1].strip())
                else:
                    nNodes = -1

                sat = int(searchString('SolverSatisfiable:',lsLines)[0].split(':')[1].strip())
                if sat==0 and nodeLimit>0 and nNodes==nodeLimit:
                    sat = ''
                    solverNodeOut = 1
                else:
                    solverNodeOut = 0

    if sat==1:
        sat = 'yes'
    if sat==0:
        sat = 'no'

    #output = ','.join([str(x) for x in [instance,model,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat]])
    return instance,model,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat


def readInstanceOptions():
    global instanceOptions    
    fn = './instance-options.txt'
    if os.path.isfile(fn):
        lsLines = readFile(fn)
        m = {}
        for ln in lsLines:
            lss = ln.split(': ')
            m[lss[0]] = lss[1]
        lsKeys = ['savilerowOptions','solverTimeLimit','solverNodeLimit','solverMinTime','solverMinNode','solverTimeLimitPrefix','solverNodeLimitPrefix','solverFlags','solver','nEvaluations','essenceModel','eprimeModel','solverRandomSeedArg']
        for key in lsKeys:
            if key in m.keys():
                instanceOptions[key] = m[key]
        instanceOptions['solverTimeLimit'] = int(instanceOptions['solverTimeLimit'])
        instanceOptions['solverNodeLimit'] = int(instanceOptions['solverNodeLimit'])
        instanceOptions['solverMinTime'] = float(instanceOptions['solverMinTime'])
        instanceOptions['solverMinNode'] = int(instanceOptions['solverMinNode'])
        instanceOptions['nEvaluations'] = int(instanceOptions['nEvaluations'])


def readGeneratorOptions():
    global generatorOptions    
    fn = './generator-options.txt'
    if os.path.isfile(fn):
        lsLines = readFile(fn)
        m = {}
        for ln in lsLines:
            lss = ln.split(': ')
            m[lss[0]] = lss[1]
        lsKeys = ['savilerowOptions','solverFlags','solverRandomSeedArg','solver','essenceModel','eprimeModel']
        for key in lsKeys:
            if key in m.keys():
                generatorOptions[key] = m[key]

def run(args):
    global instanceOptions
    global generatorOptions

    startTime = time.time()

    k = 1
    candidateId = int(args[k])
    k = k + 1
    instanceId = args[k]
    k = k + 1
    seed = int(args[k])
    k = k + 1
    instanceName = args[k]
    k = k + 1
    params = args[k:]

    print(' '.join(args))
    
    problem = instanceName
    paramDict = paramsToDict(params)

    # update param values of log-transform-params, since irace doesn't support non-positive log-param
    metaFn = None
    if os.path.isfile('./params.irace.meta'):
        metaFn = './params.irace.meta'
    elif os.path.isfile('../params.irace.meta'):
        metaFn = '../params.irace.meta'
    if metaFn is not None:
        with open(metaFn,'rt') as f:
            lsMeta = f.readlines()
        for ln in lsMeta:
            ln = ln[0:-1]
            param = ln.split(' ')[0]
            delta = int(ln.split(' ')[1])
            paramDict[param] = str(int(paramDict[param]) - delta)

    # set random seed
    random.seed(seed)

    # temporary files that will be removed at the end
    lsTempOutFiles = []

    # read options
    readInstanceOptions()
    readGeneratorOptions()

    baseFn = '-'.join([str(i) for i in [candidateId,seed]])

    
    # output headers
    genHeader = ','.join(['instance','model','SRMemOut','SRTimeOut','SRTime','solverMemOut','solverTimeOut','solverTime','solverNodeOut','nNodes','sat']) # gen output file
    outHeader = ','.join(['feasible','instance','model','seed','SRMemOut','SRTimeOut','SRTime','solverMemOut','solverTimeOut','solverTime','solverNodeOut','nNodes','sat']) # inst output file

    # output files
    genInstFn = 'gen-inst-' + baseFn + '.param'
    genOutFn = 'gen-out-' + baseFn
    instFn = 'inst-' + baseFn + '.param'
    outFn = 'out-' + baseFn

    
    #---------- generate instance
    
    # param file for the generator
    genInstFn = 'gen-inst-' + baseFn + '.param'
    print("\nGenerating " + genInstFn + '...')
    lsLines = ['letting ' + key + ' be ' + str(val) for key, val in paramDict.items()]
    with open(genInstFn, 'wt') as f:
        f.write('\n'.join(lsLines))

    # solve and save output
    print("\nSolving " + genInstFn + '...')
    [SRMemOut, infoFn, inforFn, minionFn, solutionFn, dimacsFn, cmd] = call_conjure_solve(conjureOptions=generatorOptions, paramFile=genInstFn, essenceModelFn=generatorOptions['essenceModel'], eprimeModelFn=os.path.basename(generatorOptions['eprimeModel']), nodeLimit=0, timeLimit=0, rndSeed=seed, modelDir=os.path.dirname(generatorOptions['eprimeModel']))
    instance,model,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat = parseSRInfoFile(SRMemOut,infoFn,nodeLimit=0)
    output = ','.join([str(val) for val in [instance,model,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat]])
    lsLines = [cmd,'','','Final results: ',genHeader,output]
    with open(genOutFn,'wt') as f:
        f.write('\n'.join(lsLines))


    # update list of temporary files
    lsTempOutFiles.extend([infoFn, inforFn, minionFn, solutionFn, dimacsFn])

    # process results
    if len(solutionFn) == 0: # no instances generated
        print('No instance file generated. Exitting...')
        deleteFile(lsTempOutFiles)
        output = '0,' + instFn.split('.')[0] + ''.join(','*(len(outHeader.split(','))-2))
        totalWrapperTime = time.time() - startTime
        returnedVal = 1 # if the generator configuration is infeasible, penalise it heavier than all other cases
        lsLines = ['','Total time: ' + str(totalWrapperTime),'','Final results: ',outHeader,output,str(returnedVal)]
        print('\n'.join(lsLines))
        return
    else:   # at least one instance is generated
        chosenSolutionFn = random.choice(solutionFn)
        copyfile(chosenSolutionFn, instFn)
        deleteFile(lsTempOutFiles)

    # delete temporary files
    deleteFile(lsTempOutFiles)
    lsTempOutFiles = []

    #----- evaluate the generated instance

    # for diversification, not being used atm
    nEvaluated = 0
    lsSolverTime = []
    lsSolverNodes = []

    # solve with multiple random seeds and record results
    isSucceedeed = True
    lsOutputLines = []
    print("\nSolving " + instFn + '...\n')
    for i in range(instanceOptions['nEvaluations']):
        print("With random seed " + str(i) + '\n')
        [SRMemOut, infoFn, inforFn, minionFn, solutionFn, dimacsFn, cmd] = call_conjure_solve(conjureOptions=instanceOptions, paramFile=instFn, essenceModelFn=instanceOptions['essenceModel'], eprimeModelFn=os.path.basename(instanceOptions['eprimeModel']), nodeLimit=instanceOptions['solverNodeLimit'], timeLimit=instanceOptions['solverTimeLimit'], rndSeed=i, modelDir=os.path.dirname(instanceOptions['eprimeModel']))
        
        # update list of temporary files
        lsTempOutFiles.extend([inforFn, minionFn, solutionFn, dimacsFn])
        
        instance,model,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat = parseSRInfoFile(SRMemOut,infoFn,nodeLimit=instanceOptions['solverNodeLimit'])
        output = ','.join([str(val) for val in [1,instance,model,i,SRMemOut,SRTimeOut,SRTime,solverMemOut,solverTimeOut,solverTime,solverNodeOut,nNodes,sat]])
        lsOutputLines.append(output)
        nEvaluated += 1
        lsSolverTime.append(solverTime)
        lsSolverNodes.append(nNodes)

        # instance violates one of the criteria
        returnedVal = None        
        if SRMemOut==1 or SRTimeOut==1 or solverMemOut==1 or solverTimeOut==1 or solverNodeOut==1 or sat=='no':
            returnedVal = 0
        elif instanceOptions['solverMinNode']>0 and nNodes<instanceOptions['solverMinNode']:
            returnedVal = -nNodes
        elif instanceOptions['solverMinTime']>0 and solverTime<instanceOptions['solverMinTime']:
            returnedVal = -solverTime

        # delete temporary files
        deleteFile(lsTempOutFiles)

        if returnedVal is not None:
            isSucceedeed = False
            break

    # instance satisfies our criteria
    if isSucceedeed:
        if instanceOptions['solverMinNode']>0:
            returnedVal = -instanceOptions['solverMinNode']
        else:
            returnedVal = -instanceOptions['solverMinTime']

    totalWrapperTime = time.time() - startTime
    print("Total time: " + str(totalWrapperTime) + '\n')

    # print results
    print("\nFinal results:")
    print(outHeader)
    print('\n'.join(lsOutputLines))
    print(returnedVal)

    # delete temporary files
    deleteFile(lsTempOutFiles)


def debug():
    random.seed(123)

    params_ppp = ' '.join(["-n_periods_min 25",
                "-n_periods_max 40",
                "-n_boats_min 20",
                "-n_boats_max 40",
                "-capacity_range_min 10", 
                "-capacity_range_max 40", 
                "-capacity_range_sum_lb_ratio 20", 
                "-capacity_range_sum_ub_ratio 60", 
                "-crew_range_min 10", 
                "-crew_range_max 40", 
                "-crew_range_sum_lb_ratio 20", 
                "-crew_range_sum_ub_ratio 60"])

    params = params_ppp

    for i in range(1):
        seed = random.randint(1,9999)
        args = ('wrapper.py 1 1 ' + str(seed) + ' ppp ' + params).split(' ') 
        run(args)


def main():
    run(sys.argv)

#debug()

main()
