#!/usr/bin/env Rscript

# read a parameter definition in irace's format and check if there is any log-scale parameters. If there are, shift their domain so that the lower bound is >0, as irace doesn't support non-positive log-scale parameters. A .meta (text) file recording the information of the shifting is also generated.
# syntax: ./read-log-parameter.R <parameter-definition-file>
# example: ./read-log-parameter.R params.irace

source('./utils.R')
source('./readParameters.R')

args = commandArgs(trailingOnly=TRUE)
paramFn <- args[1]

metaFn <- paste(dirname(paramFn),'/',basename(paramFn),'.meta',sep='')

p <- readParameters(paramFn)

lsMeta <- c()
lsParam <- c()
for (name in p$names){
    if (p$types[[name]] %in% c('i','r')){
        lb <- p$domain[[name]][1]
        ub <- p$domain[[name]][2]
        type <- p$types[[name]]
        if (p$transform[[name]] == 'log' & lb<=0){
            delta <- 1-lb
            ub <- ub + delta
            lb <- 1
            lsMeta <- c(lsMeta,paste(name,' ',delta,sep=''))
        }
        if (p$transform[[name]] == 'log')
            type <- paste(type,',log',sep='')
        sParam <- paste(name, ' "',p$switches[[name]],'" ',type,' (',lb,',',ub,')',sep='')
    } else {
        if (length(p$domain[[name]])>1)
            cat("\nERROR: ",name," is not a fixed param!\n")
        else
            sParam <- paste(name,' "',p$switches[[name]],'" ',type,' (',p$domain[[name]][1],')',sep='')
    }
    lsParam <- c(lsParam,sParam)
}

if (length(lsMeta)>0){
    writeLines(lsMeta,con<-file(metaFn)); close(con)
    writeLines(lsParam,con<-file(paramFn)); close(con)
}

