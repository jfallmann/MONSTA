QCENV=get_always('QCENV')
QCBIN=get_always('QCBIN')
QCPARAMS = get_always('fastqc_params_QC') ?: ''

// RAW QC
process qc_raw{
    conda "$QCENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("zip") > 0)          "QC/$COMBO$CONDITION/${file(filename).getSimpleName()}.zip"
        else if (filename.indexOf("html") > 0)    "QC/$COMBO$CONDITION/${file(filename).getSimpleName()}.html"
        else null
    }

    input:
    path read

    output:
    path "*.{zip,html}", emit: fastqc_results

    script:
    """
    fastqc --quiet -t $THREADS $QCPARAMS --noextract -f fastq $read
    """
}

workflow QC_RAW{
    take: collection

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

    samples_ch = Channel.fromPath(SAMPLES)

    qc_raw(samples_ch.collect())

    emit:
    qc = qc_raw.out.fastqc_results
}


// DEDUP QC

process qc_dedup{
    conda "$QCENV"+".yaml"
    cpus THREADS
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("zip") > 0)          "QC/$COMBO$CONDITION/${file(filename).getSimpleName()}.zip"
        else if (filename.indexOf("html") > 0)    "QC/$COMBO$CONDITION/${file(filename).getSimpleName()}.html"
        else null
    }

    input:
    path read

    output:
    path "*.{zip,html}", emit: fastqc_results

    script:
    """
    fastqc --quiet -t $THREADS $QCPARAMS --noextract -f fastq $read
    """
}

workflow QC_DEDUP{
    take: collection

    main:
   
    qc_dedup(collection.collect())

    emit:
    qc = qc_dedup.out.fastqc_results
}
