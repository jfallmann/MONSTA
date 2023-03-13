BINS = get_always('BINS')
DEUENV = get_always('DEUENV')
DEUBIN = get_always('DEUBIN')
DEUREF = get_always('DEUREF')
DEUREFDIR = "${workflow.workDir}/../"+get_always('DEUREFDIR')
DEUANNO = get_always('DEUANNO')
COUNTPARAMS = get_always('dexseq_DEU_params_COUNT') ?: ''
DEUPARAMS = get_always('dexseq_DEU_params_DEU') ?: ''
DEUREPS = get_always('DEUREPS') ?: ''
DEUCOMP = get_always('DEUCOMP') ?: ''
DEUCOMPS = get_always('DEUCOMPS') ?: ''
PVAL = get_always('DEUPVAL') ?: ''
LFC = get_always('DEULFC') ?: ''
PCOMBO = get_always('COMBO') ?: 'none'

COUNTBIN = 'featureCounts'
COUNTENV = 'countreads_de'

//DEU PROCESSES
process prepare_deu_annotation{
    conda "$COUNTENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf(".gtf") > 0)      "${DEUREFDIR}/${file(filename).getName()}"                
        else if (filename.indexOf(".log") > 0)        "LOGS/DEU/${SCOMBO}/featurecount_dexseq_annotation.log"
    }

    input:
    path anno

    output:
    path "*.gtf", emit: gtf
    path "*.log", emit: log

    script:     
    fn = file(anno).getSimpleName()
    ca = fn+"_fc_dexseq.gtf"
    da = fn+"_dexseq.gtf"
    ol = "featurecount_dexseq_annotation.log"
    sortmem = '30%'
    if (STRANDED == 'fr' || STRANDED == 'ISF'){
            stranded = '-s'
        }else if (STRANDED == 'rf' || STRANDED == 'ISR'){
            stranded = '-s'
        }else{
            stranded = ''
    }
    """
    mkdir -p TMP; $BINS/Analysis/DEU/prepare_deu_annotation.py -f $ca $stranded $anno $da 2>> $ol
    """
}

process featurecount_dexseq{
    conda "$COUNTENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf(".count") > 0)      "DEU/${SCOMBO}/Featurecounts/${file(filename).getSimpleName()}.counts.gz"                
        else if (filename.indexOf(".log") > 0)        "LOGS/DEU/${SCOMBO}/${file(filename).getSimpleName()}/featurecounts_dexseq_unique.log"
    }

    input:
    path fls

    output:
    path "*.counts.gz", emit: fc_cts
    path "*.summary", emit: fc_summary
    path "*.log", emit: fc_log

    script: 
    anno = fls[0]
    reads = fls[1]       
    fn = file(reads).getSimpleName()
    oc = fn+".counts.gz"
    os = fn+".counts.summary"
    ol = fn+".log"
    sortmem = '30%'
    if (PAIRED == 'paired'){
        pair = "-p"
    }
    else{
        pair= ""
    }
    if (STRANDED == 'fr' || STRANDED == 'ISF'){
            stranded = '-s 1'
        }else if (STRANDED == 'rf' || STRANDED == 'ISR'){
            stranded = '-s 2'
        }else{
            stranded = ''
    }
    """
    mkdir -p TMP; $COUNTBIN -T $THREADS $COUNTPARAMS $pair $stranded -a <(zcat $anno) -o tmpcts $reads 2> $ol && head -n2 tmpcts |gzip > $oc && export LC_ALL=C; tail -n+3 tmpcts|sort --parallel=$THREADS -S $sortmem -T TMP -k1,1 -k2,2n -k3,3n -u |gzip >> $oc 2>> $ol && mv tmpcts.summary $os
    """
}

process prepare_count_table{
    conda "$DEUENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename == "COUNTS.gz")      "DEU/${SCOMBO}/Tables/${COMBO}_COUNTS.gz"
        else if (filename == "ANNOTATION.gz")      "DEU/${SCOMBO}/Tables/${COMBO}_ANNOTATION.gz"
        else if (filename == "SampleDict.gz")      "DEU/${SCOMBO}/Tables/${COMBO}_SampleDict.gz"
        else if (filename == "log")      "LOGS/DEU/${SCOMBO}/${COMBO}_prepare_count_table.log"
    }

    input:
    //path '*.count*'// from reads
    path reps

    output: 
    path "*COUNTS.gz", emit: counts
    path "*ANNOTATION.gz", emit: anno
    path "*SampleDict.gz", emit: sdict
    path "log", emit: log

    script:
    """
    ${BINS}/Analysis/build_count_table.py $DEUREPS --table COUNTS.gz --anno ANNOTATION.gz --nextflow 2> log
    """
}

process run_dexseq{
    conda "$DEUENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("_table") > 0)      "DEU/${SCOMBO}/Tables/${file(filename).getName()}"                
        else if (filename.indexOf("_figure") > 0)      "DEU/${SCOMBO}/Figures/${file(filename).getName()}" 
        else if (filename.indexOf(".html") > 0)      "DEU/${SCOMBO}/DEXSeqReport_${COMBO}_${DEUCOMP}/${file(filename).getName()}"
        else if (filename.indexOf("SESSION") > 0)      "DEU/${SCOMBO}/${file(filename).getName()}"                     
        else if (filename.indexOf("log") > 0)        "LOGS/DEU/${SCOMBO}/run_dexseq.log"
    }

    input:
    path cts
    path anno
    path ref
    path deanno

    output:
    path "*_table*", emit: tbls
    path "*_figure*", emit: figs
    path "*.html", emit: html
    path "*SESSION.gz", emit: session
    path "log", emit: log

    script:    
    outdir = "DEU"+File.separatorChar+"${SCOMBO}"
    bin = "${BINS}"+File.separatorChar+"${DEUBIN}"

    """
    mkdir -p Figures Tables DEXSeqReport_${COMBO}_${DEUCOMP}
    Rscript --no-environ --no-restore --no-save $bin $anno $cts $ref $deanno . $DEUCOMP $PCOMBO $THREADS $DEUPARAMS 2> log && mv Tables/* . && mv Figures/* . && mv DEXSeqReport_*/* .

    """
}

process filter_significant{
    conda "$DEUENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf("_table") > 0)      "DEU/${SCOMBO}/Tables/${file(filename).getName()}"                                
        else if (filename.indexOf("log") > 0)        "LOGS/DEU/filter_deseq2.log"
    }

    input:
    path tabs

    output:
    path "*_table*", emit: sigtbls
    path "log", emit: log

    script:  
    """
    set +o pipefail; for i in $tabs; do if [[ -s \"\${i}\" ]];then zcat \${i}| head -n1 |gzip > Sig_\${i};cp -f Sig_\${i} SigUP_\${i}; cp -f Sig_\${i} SigDOWN_\${i}; zcat \${i}| tail -n+2 |grep -v -w 'NA'|perl -F'\t' -wlane 'next if (!\$F[6] || !\$F[3]);if (\$F[6] < $PVAL && (\$F[3] <= -$LFC ||\$F[3] >= $LFC) ){{print}}' |gzip >> Sig_\${i} && zcat \${i}| tail -n+2 |grep -v -w 'NA'|perl -F'\t' -wlane 'next if (!\$F[6] || !\$F[3]);if (\$F[6] < $PVAL && (\$F[3] >= $LFC) ){{print}}' |gzip >> SigUP_\${i} && zcat \${i}| tail -n+2 |grep -v -w 'NA'|perl -F'\t' -wlane 'next if (!\$F[6] || !\$F[3]);if (\$F[6] < $PVAL && (\$F[3] <= -$LFC) ){{print}}' |gzip >> SigDOWN_\${i}; else touch Sig_\${i} SigUP\${i} SigDOWN_\${i}; fi;done 2> log
    """
}

process create_summary_snippet{
    conda "$DEUENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    publishDir "${workflow.workDir}/../" , mode: 'link',
    saveAs: {filename ->
        if (filename.indexOf(".Rmd") > 0)         "REPORTS/SUMMARY/RmdSnippets/${SCOMBO}.Rmd"                               
        else if (filename.indexOf("log") > 0)        "LOGS/DEU/filter_dexseq.log"
    }

    input:
    path de

    output:
    path "*.Rmd", emit: snps
    path "log", emit: log

    script:
    inlist = de.toString()
    // inlist = de.toList()  // { $workflow.projectDir += "$it.code,"  }
    """
    touch log; python3 $BINS/Analysis/RmdCreator.py --files $inlist --output out.Rmd --env $DEUENV --loglevel DEBUG 2>> log
    """
}

process collect_dexseq{
    conda "$DEUENV"+".yaml"
    cpus THREADS
	cache 'lenient'
    //validExitStatus 0,1

    input:
    path de

    script:
    """
    echo "$de DONE"
    """
}

workflow DEU{ 
    take: collection

    main:
    
    MAPPEDSAMPLES = LONGSAMPLES.collect{
        element -> return "${workflow.workDir}/../MAPPED/${COMBO}/"+element+"_mapped_sorted_unique.bam"
    }

    mapsamples_ch = Channel.fromPath(MAPPEDSAMPLES)
    mapsamples_ch.subscribe {  println "MAP: $it \t COMBO: ${COMBO} SCOMBO: ${SCOMBO} LONG: ${LONGSAMPLES}"  }
    annofile = Channel.fromPath(DEUANNO)
    //annofile.subscribe {  println "ANNO: $it \t COMBO: ${COMBO} SCOMBO: ${SCOMBO} LONG: ${LONGSAMPLES}"  }

    featurecount_dexseq(annofile.combine(mapsamples_ch.collate(1)))
    prepare_deu_annotation(annofile)
    prepare_count_table(featurecount_dexseq.out.fc_cts.collect())
    run_dexseq(prepare_count_table.out.counts, prepare_count_table.out.anno, annofile, prepare_deu_annotation.out.gtf)
    filter_significant(run_dexseq.out.tbls)
    create_summary_snippet(run_dexseq.out.tbls.concat(run_dexseq.out.figs.concat(run_dexseq.out.session)).collect())
    collect_dexseq(filter_significant.out.sigtbls.collect())

    emit:
    tbls = run_dexseq.out.tbls
    sigtbls = filter_significant.out.sigtbls
    figs = run_dexseq.out.figs
    snps = create_summary_snippet.out.snps
}