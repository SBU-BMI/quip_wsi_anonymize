import json
import pandas as pd
import sys
import subprocess
import uuid
import os
import argparse
from shutil import copyfile

error_info = {}
error_info["no_error"] = { "code":0, "msg":"no-error" }
error_info["anonymize_error"] = { "code":701, "msg":"error_with_anonymization" }

parser = argparse.ArgumentParser(description="Remove lable image from WSI.")
parser.add_argument("--inpmeta",nargs="?",default="quip_manifest.csv",type=str,help="input manifest (metadata) file.")
parser.add_argument("--outmeta",nargs="?",default="quip_manifest.csv",type=str,help="output manifest (metadata) file.")
parser.add_argument("--errfile",nargs="?",default="quip_wsi_error_log.json",type=str,help="error log file.")
parser.add_argument("--inpdir",nargs="?",default="/data/images",type=str,help="input folder.")
parser.add_argument("--outdir",nargs="?",default="/data/output",type=str,help="output folder.")

def anonymize_image(ifname,file_uuid,file_ext,outdir):
    ierr = error_info["no_error"]
    out_fdir = outdir+"/"+file_uuid
    if not os.path.exists(out_fdir): 
        os.makedirs(out_fdir)
    copyfile(ifname,os.path.join(out_fdir+"/"+file_uuid+file_ext));
    cmd = "python anonymize-slide/anonymize-slide.py " + out_fdir+"/"+file_uuid+file_ext;

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.wait()

    return out_fdir+"/"+file_uuid+file_ext,ierr

def main(args):
    inp_folder = args.inpdir
    out_folder = args.outdir
    inp_manifest_fname = args.inpmeta
    out_manifest_fname = args.outmeta 
    out_error_fname = args.errfile 

    out_error_fd = open(out_folder + "/" + out_error_fname,"w");
    all_log = {}
    all_log["error"] = []
    all_log["warning"] = [] 
    try:
        inp_metadata_fd = open(inp_folder + "/" + inp_manifest_fname);
    except OSError:
        ierr = error_info["missing_file"]
        ierr["msg"] = ierr["msg"]+": " + str(inp_manifest_fname);
        all_log["error"].append(ierr)
        json.dump(all_log,out_error_fd)
        out_error_fd.close()
        sys.exit(1)

    pfinp = pd.read_csv(inp_metadata_fd,sep=',')
    out_metadata_fd  = open(out_folder + "/" + out_manifest_fname,"w")
    cols = ['file_uuid','anonymized_filename','anonymize_error_code','anonymize_error_msg'];
    one_row = pd.DataFrame(columns=cols);
    no_header = 0
    for file_idx in range(len(pfinp["path"])):
        if str(pfinp["manifest_error_code"][file_idx])==str(error_info["no_error"]["code"]):
            file_row  = pfinp["path"][file_idx]
            file_uuid = pfinp["file_uuid"][file_idx]
            print("Processing: ",file_row)

            ifname = inp_folder+"/"+file_row
            ofname = file_uuid
            ofext  = pfinp["file_ext"][file_idx]
            anonymized_filename,ierr = anonymize_image(ifname,ofname,ofext,out_folder)
            one_row.at[0,"file_uuid"] = file_uuid
            one_row.at[0,"anonymized_filename"] = anonymized_filename;
            one_row.at[0,"anonymize_error_code"] = str(ierr["code"]);
            one_row.at[0,"anonymize_error_msg"]  = ierr["msg"];
            if str(ierr["code"]) != str(error_info["no_error"]["code"]):
                ierr["row_idx"] = file_idx
                ierr["filename"] = file_row 
                ierr["file_uuid"] = file_uuid
                all_log["error"].append(ierr)

            if no_header == 1:
                one_row.to_csv(out_metadata_fd,mode="a",index=False,header=False)
            else:
                one_row.to_csv(out_metadata_fd,mode="w",index=False)
                no_header = 1

    json.dump(all_log,out_error_fd)

    inp_metadata_fd.close()
    out_metadata_fd.close()
    out_error_fd.close()
 
    sys.exit(0)

if __name__ == "__main__":
    args = parser.parse_args(sys.argv[1:]);
    main(args)
