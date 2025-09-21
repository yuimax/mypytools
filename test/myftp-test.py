import myftp

myftp.verbose(False)
target_dir = './sample'

for name in myftp.get_ftp_names():
    try:
        myftp.remove_tree(name, target_dir)
        myftp.upload_tree(name, target_dir)
        myftp.ls(name, target_dir)
        print()
    except Exception as e:
        print(f"ERROR: {e}")
