import os

src_path = 'src'
for d in os.listdir(src_path):
    full_path = os.path.join(src_path, d)
    if os.path.isdir(full_path) and 'mko' in d:
        print(f"Directory: {repr(d)}, len={len(d)}, underscores={d.count('_')}")
        # Check if data/processing exists
        data_path = os.path.join(full_path, 'data', 'processing')
        if os.path.exists(data_path):
            print("  data/processing exists!")
            for f in os.listdir(data_path):
                print(f"    {f}")
