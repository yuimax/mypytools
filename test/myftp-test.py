import myftp

myftp.verbose(False)
target_dir = './sample'

for ftp_name in myftp.get_ftp_names():
    try:
        myftp.remove_tree(ftp_name, target_dir)
        myftp.upload_tree(ftp_name, target_dir)
        myftp.ls(ftp_name, target_dir)
        print()
    except Exception as e:
        print(f"ERROR: {e}")
