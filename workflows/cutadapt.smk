TRIMBIN, TRIMENV = env_bin_from_config(config,'TRIMMING')

if paired == 'paired':
    rule cutadapt_trim:
        input:  r1 = lambda wildcards: "FASTQ/{rawfile}_R1.fastq.gz".format(rawfile=[x for x in SAMPLES if x.split(os.sep)[-1] in wildcards.file][0]) if not prededup else "DEDUP_FASTQ/{combo}/{file}_R1_dedup.fastq.gz",
                r2 = lambda wildcards: "FASTQ/{rawfile}_R2.fastq.gz".format(rawfile=[x for x in SAMPLES if x.split(os.sep)[-1] in wildcards.file][0]) if not prededup else "DEDUP_FASTQ/{combo}/{file}_R2_dedup.fastq.gz"
        output: o1 = "TRIMMED_FASTQ/{combo}/{file}_R1_val_1.fq.gz" if not prededup else "TRIMMED_FASTQ/{combo}/{file}_R1_dedup_val_1.fq.gz",
                o2 = "TRIMMED_FASTQ/{combo}/{file}_R2_val_2.fq.gz" if not prededup else "TRIMMED_FASTQ/{combo}/{file}_R2_dedup_val_2.fq.gz"
        log:    "LOGS/{combo}/{file}_trim.log"
        conda: ""+TRIMENV+".yaml"
        container: "oras://jfallmann/monsda:"+TRIMENV+""
        threads: min(int(MAXTHREAD/8),4) if min(int(MAXTHREAD/8),4) >= 1 else (4 if int(MAXTHREAD) >= 4 else 1)
        params: odir=lambda wildcards, output:os.path.dirname(output.o1),
                tpara = lambda wildcards: tool_params(wildcards.file, None, config, "TRIMMING", TRIMENV)['OPTIONS'].get('TRIM', ""),
                trim=TRIMBIN
        shell:  "{params.trim} {params.tpara} --cores {threads} -o {output.o1} -p {output.o2} {input.r1} {input.r2} &> {log}"

    rule cutadapt_rename:
        input:  o1 = rules.cutadapt_trim.output.o1,
                o2 = rules.cutadapt_trim.output.o2
        output: r1 = "TRIMMED_FASTQ/{combo}/{file}_R1_trimmed.fastq.gz",
                r2 = "TRIMMED_FASTQ/{combo}/{file}_R2_trimmed.fastq.gz"
        conda: ""+TRIMENV+".yaml"
        container: "oras://jfallmann/monsda:"+TRIMENV+""
        threads: 1
        shell:  "mv {input.o1} {output.r1} && mv {input.o2} {output.r2}"

else:
    rule cutadapt_trim:
        input:  r1 = lambda wildcards: "FASTQ/{rawfile}.fastq.gz".format(rawfile=[x for x in SAMPLES if x.split(os.sep)[-1] in wildcards.file][0]) if not prededup else "DEDUP_FASTQ/{combo}/{file}_dedup.fastq.gz"
        output: o1 = "TRIMMED_FASTQ/{combo}/{file}_trimmed.fq.gz" if not prededup else "TRIMMED_FASTQ/{combo}/{file}_dedup_trimmed.fq.gz"
        log:    "LOGS/{combo}/{file}_trim.log"
        conda: ""+TRIMENV+".yaml"
        container: "oras://jfallmann/monsda:"+TRIMENV+""
        threads: min(int(MAXTHREAD/8),4) if min(int(MAXTHREAD/2),4) >= 1 else (4 if int(MAXTHREAD) >= 4 else 1)
        params: odir=lambda wildcards, output: os.path.dirname(output.o1),
                tpara = lambda wildcards:tool_params(wildcards.file, None, config, "TRIMMING", TRIMENV)['OPTIONS'].get('TRIM', ""),
                trim=TRIMBIN,
        shell:  "{params.trim} {params.tpara} --cores {threads} -o {output.o1} {input.r1} > {log}"

    rule cutadapt_rename:
        input:  o1 = rules.cutadapt_trim.output.o1
        output: r1 = "TRIMMED_FASTQ/{combo}/{file}_trimmed.fastq.gz"
        conda: ""+TRIMENV+".yaml"
        container: "oras://jfallmann/monsda:"+TRIMENV+""
        threads: 1
        shell:  "mv {input.o1} {output.r1}"
