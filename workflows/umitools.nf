DEDUPENV=get_always('DEDUPENV')
DEDUPBIN=get_always('DEDUPBIN')

WHITELISTPARAMS = get_always('picard_params_WHITELIST') ?: ''
EXTRACTPARAMS = get_always('umitools_params_EXTRACT') ?: ''


process collect_dedup{
    input:
    path check
    val checker

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

    publishDir "${workflow.workDir}/../" , mode: 'copy',
    saveAs: {filename ->
        if (filename.indexOf("_whitelist") > 0)          "FASTQ/$COMBO$CONDITION/${file(filename).getSimpleName()}_whitelist"
        else if (filename.indexOf("log") > 0)    "LOGS/$COMBO$CONDITION/dedup_whitelist.log"
        else null
    }

    input:
    path samples
        
    output:
    path "*_whitelist", emit: wl

    script:
    if paired{
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
            mkdir tmp && $DEDUPBIN whitelist $WHITELISTPARAMS --temp-dir tmp --log=wl.log --stdin=$r1 --stdout=$out
        """
    }
}

process extract{
    conda "$DEDUPENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'copy',
    saveAs: {filename ->
        if (filename.indexOf("_dedup.fastq.gz") > 0)          "DEDUP_FASTQ/$COMBO$CONDITION/${file(filename)}"
        else if (filename.indexOf("log") > 0)    "LOGS/$COMBO$CONDITION/dedup_extract.log"
        else null
    }

    input:
    path samples
        
    output:
    path "*_dedup.fastq.gz", emit: ex

    script:
    if paired{
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
            mkdir tmp && $DEDUPBIN extract $EXTRACTPARAMS --temp-dir tmp --log=ex.log --stdin=$r1 --stdout=$out
        """
    }
}

workflow DEDUPEXTRACT{
    take: collection

    main:
    //SAMPLE CHANNELS
    if (PAIRED == 'paired'){
        T1SAMPLES = LONGSAMPLES.collect{
            element -> return "${workflow.workDir}/../FASTQ/$COMBO"+element+"_R1.fastq.gz"
        }
        T1SAMPLES.sort()
        T2SAMPLES = LONGSAMPLES.collect{
            element -> return "${workflow.workDir}/../FASTQ/$COMBO"+element+"_R2.fastq.gz"
        }
        T2SAMPLES.sort()
        dedup_samples_ch = Channel.fromPath(T1SAMPLES).join(Channel.fromPath(T2SAMPLES))

    }else{
        T1SAMPLES = LONGSAMPLES.collect{
            element -> return "${workflow.workDir}/../FASTQ/$COMBO"+element+".fastq.gz"
        }
        T1SAMPLES.sort()
        dedup_samples_ch = Channel.fromPath(T1SAMPLES)
    }

    
    collect_dedup(maplogs.collect())
    if WHITELISTPARAMS != ''{
        umitools_whitelist(collect_dedup.out.done.collect(), dedup_samples_ch)
        umitools_extract(umitools_whitelist.out.done.collect(), dedup_samples_ch)        
    }
    else{
        umitools_extract(collect_dedup.out.done.collect(), dedup_samples_ch)        
    }
    
    emit:
    if WHITELISTPARAMS != ''{
        white = whitelist.out.wl
        extract = extract.out.ex
    }
    else{
        extract = extract.out.ex
    }
}


