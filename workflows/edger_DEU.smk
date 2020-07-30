DEUBIN, DEUENV = env_bin_from_config3(config,'DEU')
COUNTBIN, COUNTENV = ['featureCounts','countreads']#env_bin_from_config2(SAMPLES,config,'COUNTING')

outdir = "DEU/EDGER/"
comparison = comparable_as_string2(config,'DEU')
compstr = [i.split(":")[0] for i in comparison.split(",")]

rule themall:
    input:  all = expand("{outdir}EDGER_DEU_All_Conditions_MDS.png", outdir=outdir),
            allsum = expand("{outdir}EDGER_DEU_All_Conditions_sum_MDS.png", outdir=outdir),
            tbl = expand("{outdir}EDGER_DEU_All_Conditions_normalized_table.tsv.gz", outdir=outdir),
            bcv = expand("{outdir}EDGER_DEU_All_Conditions_BCV.png", outdir=outdir),
            qld = expand("{outdir}EDGER_DEU_All_Conditions_QLDisp.png", outdir=outdir),
            dift = expand("{outdir}EDGER_DEU_{comparison}_exons_{sort}.tsv.gz", outdir=outdir, comparison=compstr, sort=["logFC-sorted","pValue-sorted"]),
            sigdift = expand("{outdir}Sig_EDGER_DEU_{comparison}_exons_{sort}.tsv.gz", outdir=outdir, comparison=compstr, sort=["logFC-sorted","pValue-sorted"]),
            plot = expand("{outdir}EDGER_DEU_{comparison}_MD.png", outdir=outdir, comparison=compstr),
            session = expand("{outdir}EDGER_DEU_SESSION.gz", outdir=outdir)

rule featurecount_unique:
    input:  reads = "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam"
    output: tmp   = temp(expand("{outdir}Featurecounts_DEU_edger/{{file}}_tmp.counts", outdir=outdir)),
            cts   = "DEU/Featurecounts_DEU/{file}_mapped_sorted_unique.counts"
    log:    "LOGS/{file}/featurecounts_DEU_edger_unique.log"
    conda:  "nextsnakes/envs/"+COUNTENV+".yaml"
    threads: MAXTHREAD
    params: countb = COUNTBIN,
            anno  = lambda wildcards: str.join(os.sep,[config["REFERENCE"],os.path.dirname(genomepath(wildcards.file, config)),tool_params(wildcards.file, None, config, 'DEU')['ANNOTATION']]),
            cpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, "DEU")['OPTIONS'][0].items()),
            paired   = lambda x: '-p' if paired == 'paired' else '',
            stranded = lambda x: '-s 1' if stranded == 'fr' else '-s 2' if stranded == 'rf' else ''
    shell:  "{params.countb} -T {threads} {params.cpara} {params.paired} {params.stranded} -a <(zcat {params.anno}) -o {output.tmp} {input.reads} 2> {log} && head -n2 {output.tmp} > {output.cts} && export LC_ALL=C; tail -n+3 {output.tmp}|sort --parallel={threads} -S 25% -T TMP -k1,1 -k2,2n -k3,3n -u >> {output.cts} && mv {output.tmp}.summary {output.cts}.summary"

rule prepare_count_table:
    input:   cnd  = expand(rules.featurecount_unique.output.cts, file=samplecond(SAMPLES,config))
    output:  tbl  = expand("{outdir}Tables/COUNTS.gz",outdir=outdir),
             anno = expand("{outdir}Tables/ANNOTATION.gz",outdir=outdir)
    log:     expand("LOGS/{outdir}prepare_count_table.log",outdir=outdir)
    conda:   "nextsnakes/envs/"+DEUENV+".yaml"
    threads: 1
    params:  dereps = lambda wildcards, input: get_reps(input.cnd,config,'DEU'),
             bins = BINS,
             tpara  = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(samplecond(SAMPLES,config)[0], None ,config, "DEU")['OPTIONS'][1].items())
    shell: "{params.bins}/Analysis/build_count_table_id.py {params.dereps} --table {output.tbl} --anno {output.anno} {params.tpara} --loglevel DEBUG 2> {log}"

rule run_edger:
    input:  tbl = rules.prepare_count_table.output.tbl,
            anno = rules.prepare_count_table.output.anno,
    output: rules.themall.input.all,
            rules.themall.input.allsum,
            rules.themall.input.tbl,
            rules.themall.input.bcv,
            rules.themall.input.qld,
            rules.themall.input.dift,
            rules.themall.input.plot,
            rules.themall.input.session
    log:    expand("LOGS/{outdir}run_edger.log",outdir=outdir)
    conda:  "nextsnakes/envs/"+DEUENV+".yaml"
    threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
    params: bins   = str.join(os.sep,[BINS,DEUBIN]),
            outdir = outdir,
            compare = comparison
    shell: "Rscript --no-environ --no-restore --no-save {params.bins} {input.anno} {input.tbl} {params.outdir} {params.compare} {threads} 2> {log}"

rule filter_significant_edgerDEU:
    input:  dift = rules.run_edger.output.dift
    output: sigdift  = rules.themall.input.sigdift
    log:    expand("LOGS/{outdir}filter_edgerDEU.log",outdir=outdir)
    conda:  "nextsnakes/envs/"+DEUENV+".yaml"
    threads: 1
    shell: "cd {outdir} && for i in EDGER_*.tsv.gz;do if [ -s \"$i\" ];then for i in EDGER_DE*pValue-sorted.tsv.gz;do zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F$'\t' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < 0.05 && ($F[2] <= -1.5 ||$F[2] >= 1.5) ){{print}}' |gzip > $i\_Sig.tsv.gz;done && for i in *pValue-sorted.tsv;do cat $i| tail -n+2 |grep -v -w 'NA'|perl -F$'\t' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < 0.05 && ($F[2] >= 1.5) ){{print}}' |gzip > $i\_SigUP.tsv.gz;done && for i in *pValue-sorted.tsv;do cat $i| tail -n+2 |grep -v -w 'NA'|perl -F$'\t' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < 0.05 && ($F[2] <= -1.5) ){{print}}' |gzip > $i\_SigDOWN.tsv.gz;done;else touch Sig_$i SigUP_$i SigDOWN_$i; fi;done"
