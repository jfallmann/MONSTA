DEDUPENV=get_always('DEDUPENV')
DEDUPBIN=get_always('DEDUPBIN')

WHITELISTPARAMS = get_always('umitools_params_WHITELIST') ?: ''
EXTRACTPARAMS = get_always('umitools_params_EXTRACT') ?: ''


process collect_extract{
    input:
    path check

    output:
    path "collect.txt", emit: done

    script:
    """
    echo "$check Collection successful!" > collect.txt
    """
}


process whitelist{
    conda "$DEDUPENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("_whitelist") > 0)         "FASTQ/$COMBO$CONDITION/${file(filename).getSimpleName()}_whitelist"
        else if (filename.indexOf("log") > 0)           "LOGS/$COMBO$CONDITION/DEDUP/dedup_whitelist.log"
        else null
    }

    input:
    path samples
        
    output:
    path "*_whitelist", emit: wl

    script:
    if (PAIRED == 'paired'){
        r1=samples[0]
        r2=samples[1]
        out=samples[0].getSimpleName()+"_whitelist"
        """
            mkdir tmp && $DEDUPBIN whitelist $WHITELISTPARAMS --temp-dir tmp --log=wl.log --stdin=$r1 --read2-in=$r2 --stdout=$out
        """
    }
    else{
        out=samples.getSimpleName()+"_whitelist"
        """
            mkdir tmp && $DEDUPBIN whitelist $WHITELISTPARAMS --temp-dir tmp --log=wl.log --stdin=$samples --stdout=$out
        """
    }
}

process extract{
    conda "$DEDUPENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("_dedup.fastq.gz") > 0)      "DEDUP_FASTQ/$COMBO$CONDITION/${file(filename).getSimpleName()}.fastq.gz"
        else if (filename.indexOf("log") > 0)             "LOGS/$COMBO$CONDITION/DEDUP/dedup_extract.log"
        else null
    }

    input:
    path samples
        
    output:
    path "*_dedup.fastq.gz", emit: ex

    script:
    if (PAIRED == 'paired'){
        r1=samples[0]
        r2=samples[1]
        out=samples[0].getSimpleName()+"_dedup.fastq.gz"
        out2=samples[1].getSimpleName()+"_dedup.fastq.gz"
        """
            mkdir tmp && $DEDUPBIN extract $EXTRACTPARAMS --temp-dir tmp --log=ex.log --stdin=$r1 --read2-in=$r2 --stdout=$out --read2-out=$out2
        """
    }
    else{
        out=samples.getSimpleName()+"_dedup.fastq.gz"
        """
            mkdir tmp && $DEDUPBIN extract $EXTRACTPARAMS --temp-dir tmp --log=ex.log --stdin=$samples --stdout=$out
        """
    }
}


process extract_wl{
    conda "$DEDUPENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("_dedup.fastq.gz") > 0)      "DEDUP_FASTQ/$COMBO$CONDITION/${file(filename).getSimpleName()}.fastq.gz"
        else if (filename.indexOf("log") > 0)             "LOGS/$COMBO$CONDITION/DEDUP/dedup_extract.log"
        else null
    }

    input:
    path wl
    path samples
        
    output:
    path "*_dedup.fastq.gz", emit: ex

    script:
    if (PAIRED == 'paired'){
        r1=samples[0]
        r2=samples[1]
        out=samples[0].getSimpleName()+"_dedup.fastq.gz"
        out2=samples[1].getSimpleName()+"_dedup.fastq.gz"
        """
            mkdir tmp && $DEDUPBIN extract $EXTRACTPARAMS --whitelist=$wl --temp-dir tmp --log=ex.log --stdin=$r1 --read2-in=$r2 --stdout=$out --read2-out=$out2
        """
    }
    else{
        out=samples.getSimpleName()+"_dedup.fastq.gz"
        """
            mkdir tmp && $DEDUPBIN extract $EXTRACTPARAMS --whitelist=$wl --temp-dir tmp --log=ex.log --stdin=$samples --stdout=$out
        """
    }
}


workflow DEDUPEXTRACT{
    take: 
    collection

    main:
        //SAMPLE CHANNELS
    if (PAIRED == 'paired'){
        SAMPLES = SAMPLES.collect{
            element -> return "${workflow.workDir}/../FASTQ/"+element+"_R{1,2}.*fastq.gz"
        }
    }else{
        SAMPLES=SAMPLES.collect{
            element -> return "${workflow.workDir}/../FASTQ/"+element+".fastq.gz"
        }
    }

    if (collection.collect().contains('MONSDA.log') || collection.collect().isEmpty()){
        if (PAIRED == 'paired'){
            collection = Channel.fromPath(SAMPLES).collate( 2 )
        }
        else{
            collection = Channel.fromPath(SAMPLES).collate( 1 )
        }
    }
       
    if (WHITELISTPARAMS != ''){
        whitelist(collection)
        extract_wl(whitelist.out.done.wl, collection)
    }
    else{
        extract(collection)
    }
    
    emit:
    ex = extract.out.ex
    
}